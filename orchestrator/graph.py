import uuid
from langgraph.graph import StateGraph, END
from orchestrator.state import PipelineState
from agents.data.agent import data_node
from agents.training.agent import training_node
from orchestrator.agents_mock import qa_node, release_node



def route(next_node):
    return lambda s: END if s.get("status") == "failed" else next_node

def build_graph():
    g = StateGraph(PipelineState)
    g.add_node("data", data_node)
    g.add_node("training", training_node)
    g.add_node("qa", qa_node)
    g.add_node("release", release_node)
    g.set_entry_point("data")
    g.add_conditional_edges("data", route("training"))
    g.add_conditional_edges("training", route("qa"))
    g.add_conditional_edges("qa", route("release"))
    g.add_edge("release", END)
    return g.compile()

if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"run_id": uuid.uuid4().hex[:8], "status": "running", "errors": []})
    print(result)