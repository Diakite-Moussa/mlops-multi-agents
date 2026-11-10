from quality_gate.gate import decide, load_config

BASE = {"accuracy": 0.86, "f1": 0.68, "prod_accuracy": 0.85, "regression_vs_prod": -0.01,
        "fairness_gap": 0.12, "fairness_by_attr": {}, "robustness_drop": 0.01}


def report(**kw):
    return {**BASE, **kw}


def test_config_loads():
    cfg = load_config()
    assert cfg["min_accuracy"] == 0.80


def test_reject_low_accuracy():
    d = decide(report(accuracy=0.60))
    assert d["decision"] == "reject" and "accuracy" in d["reasons"][0]


def test_reject_regression_vs_production():
    assert decide(report(regression_vs_prod=0.05))["decision"] == "reject"


def test_reject_unfair_model():
    assert decide(report(fairness_gap=0.40))["decision"] == "reject"


def test_reject_fragile_model():
    assert decide(report(robustness_drop=0.20))["decision"] == "reject"


def test_good_model_needs_human():
    assert decide(report())["decision"] == "needs_human"


def test_low_risk_is_auto_approved():
    d = decide(report(accuracy=0.93, regression_vs_prod=-0.02, fairness_gap=0.02))
    assert d["decision"] == "auto_approve"


def test_first_release_is_never_auto_approved():
    d = decide(report(accuracy=0.95, regression_vs_prod=None, fairness_gap=0.0))
    assert d["decision"] == "needs_human"
