from core import training_ops
from orchestrator.tracing import traced


def run_training(state, client=None, seed: int = training_ops.SEED) -> dict:
    df = training_ops.load_dataset(state["dataset_uri"], state["dataset_hash"], client=client)
    model, metrics = training_ops.entrainer(df, seed)
    model_uri = training_ops.publish_model(model, client=client)
    training_ops.log_run(
        params={"model": "logistic_regression", "seed": seed,
                "test_size": training_ops.TEST_SIZE, "n_rows": len(df)},
        metrics=metrics, dataset_uri=state["dataset_uri"],
        dataset_hash=state["dataset_hash"], model_uri=model_uri)
    return {"model_uri": model_uri, "metrics": metrics}


@traced("training")
def training_node(state):
    return run_training(state)