from pathlib import Path

import yaml

from orchestrator.tracing import log_event, traced

CONFIG_PATH = Path(__file__).with_name("gate.yaml")


def load_config(path=CONFIG_PATH) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def decide(report: dict, cfg: dict | None = None) -> dict:
    """Décision déterministe : reject | auto_approve | needs_human."""
    cfg = cfg or load_config()
    reg = report.get("regression_vs_prod")
    reasons = []
    if report["accuracy"] < cfg["min_accuracy"]:
        reasons.append(f"accuracy {report['accuracy']} < {cfg['min_accuracy']}")
    if reg is not None and reg > cfg["max_regression_vs_prod"]:
        reasons.append(f"régression vs production {reg} > {cfg['max_regression_vs_prod']}")
    if report["fairness_gap"] > cfg["max_fairness_gap"]:
        reasons.append(f"écart d'équité {report['fairness_gap']} > {cfg['max_fairness_gap']}")
    if report["robustness_drop"] > cfg["max_robustness_drop"]:
        reasons.append(f"perte de robustesse {report['robustness_drop']} > {cfg['max_robustness_drop']}")
    if reasons:
        return {"decision": "reject", "risk": "high", "reasons": reasons}

    auto = cfg["auto_approve"]
    low_risk = (reg is not None and reg <= 0
                and report["accuracy"] >= auto["min_accuracy"]
                and report["fairness_gap"] <= auto["max_fairness_gap"])
    if low_risk:
        return {"decision": "auto_approve", "risk": "low", "reasons": ["tous les critères faible risque sont remplis"]}
    return {"decision": "needs_human", "risk": "high", "reasons": ["approbation humaine requise"]}


@traced("gate")
def gate_node(state):
    decision = decide(state["qa_report"])
    log_event(state["run_id"], "gate", "decision", decision)
    update = {"gate_decision": decision}
    if decision["decision"] == "reject":
        update["status"] = "rejected"
        update["errors"] = state.get("errors", []) + ["gate: " + "; ".join(decision["reasons"])]
    return update
