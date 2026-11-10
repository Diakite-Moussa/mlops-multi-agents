from core import qa_ops, registry, training_ops
from orchestrator.tracing import traced


def run_qa(state, client=None) -> dict:
    df = training_ops.load_dataset(state["dataset_uri"], state["dataset_hash"], client=client)
    candidate = qa_ops.load_model(state["model_uri"], client=client)
    pointer = registry.get_production(client=client)
    production = qa_ops.load_model(pointer["model_uri"], client=client) if pointer else None
    return {"qa_report": qa_ops.build_report(candidate, df, production)}


@traced("qa")
def qa_node(state):
    return run_qa(state)
