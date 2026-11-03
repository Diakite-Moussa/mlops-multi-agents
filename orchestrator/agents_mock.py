import os
from orchestrator.tracing import traced

def _maybe_fail(name):
    if os.getenv("FAIL_AT") == name:
        raise RuntimeError(f"échec simulé dans {name}")

@traced("data")
def data_node(state):
    _maybe_fail("data")
    return {"dataset_uri": "s3://datasets/mock/v1.csv", "dataset_hash": "sha256:mock"}

@traced("training")
def training_node(state):
    _maybe_fail("training")
    return {"model_uri": "s3://models/mock/model.pkl", "metrics": {"accuracy": 0.9}}

@traced("qa")
def qa_node(state):
    _maybe_fail("qa")
    return {"qa_report": {"non_regression": "ok", "fairness_gap": 0.03}}

@traced("release")
def release_node(state):
    _maybe_fail("release")
    return {"status": "done"}