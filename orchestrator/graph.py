import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from agents.data.agent import data_node
from agents.qa.agent import qa_node
from agents.training.agent import training_node
from orchestrator.agents_mock import release_node
from orchestrator.state import PipelineState
from orchestrator.tracing import log_event
from quality_gate.gate import gate_node

STOP = ("failed", "rejected")


def route(next_node):
    return lambda s: END if s.get("status") in STOP else next_node


def after_gate(s):
    if s.get("status") in STOP:
        return END
    return "release" if s["gate_decision"]["decision"] == "auto_approve" else "approval"


def approval_node(state):
    """Pause le graphe jusqu'à la décision humaine.
    Pas de @traced ici : il intercepterait l'exception d'interruption de LangGraph."""
    answer = interrupt({"run_id": state["run_id"], "model_uri": state["model_uri"],
                        "qa_report": state["qa_report"], "gate_decision": state["gate_decision"]})
    approved = bool(answer.get("approved")) if isinstance(answer, dict) else bool(answer)
    log_event(state["run_id"], "approval", "approved" if approved else "rejected")
    if approved:
        return {"approved": True}
    return {"approved": False, "status": "rejected",
            "errors": state.get("errors", []) + ["approval: refus humain"]}


def build_graph(checkpointer=None):
    g = StateGraph(PipelineState)
    g.add_node("data", data_node)
    g.add_node("training", training_node)
    g.add_node("qa", qa_node)
    g.add_node("gate", gate_node)
    g.add_node("approval", approval_node)
    g.add_node("release", release_node)
    g.set_entry_point("data")
    g.add_conditional_edges("data", route("training"))
    g.add_conditional_edges("training", route("qa"))
    g.add_conditional_edges("qa", route("gate"))
    g.add_conditional_edges("gate", after_gate)
    g.add_conditional_edges("approval", route("release"))
    g.add_edge("release", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())


def run_pipeline(approver=None, run_id=None, app=None) -> dict:
    """Lance le pipeline. `approver(payload) -> bool` répond à la demande d'approbation humaine ;
    sans approver, le résultat contient '__interrupt__' et le pipeline reste en attente."""
    app = app or build_graph()
    run_id = run_id or uuid.uuid4().hex[:8]
    config = {"configurable": {"thread_id": run_id}}
    result = app.invoke({"run_id": run_id, "status": "running", "errors": []}, config)
    while approver and "__interrupt__" in result:
        payload = result["__interrupt__"][0].value
        result = app.invoke(Command(resume={"approved": bool(approver(payload))}), config)
    return result


if __name__ == "__main__":
    def ask(payload):
        print("\n--- Approbation humaine requise ---")
        print("modèle :", payload["model_uri"])
        print("QA     :", payload["qa_report"])
        return input("Approuver le déploiement ? (o/n) ").strip().lower() == "o"

    print(run_pipeline(approver=ask))
