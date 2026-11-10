import numpy as np
import pandas as pd
import pytest

from agents.training.agent import run_training
from core import data_ops, storage, training_ops
from tests.fakes import FakeClient


def synthetic_df(n=300):
    rng = np.random.default_rng(0)
    age = rng.integers(18, 70, n)
    hours = rng.integers(20, 60, n)
    work = rng.choice(["Private", "Gov"], n)
    score = age / 70 + hours / 60 + rng.normal(0, 0.3, n)
    return pd.DataFrame({"age": age, "workclass": work, "hours-per-week": hours,
                         "class": np.where(score > 1.1, ">50K", "<=50K")})


def setup_dataset(client):
    data = data_ops.to_csv_bytes(synthetic_df())
    uri = storage.upload_bytes("datasets", "adult/v1_test.csv", data, client=client)
    return {"dataset_uri": uri, "dataset_hash": storage.sha256_bytes(data)}


@pytest.fixture(autouse=True)
def no_mlflow(monkeypatch):
    monkeypatch.setattr("core.training_ops.log_run", lambda *a, **k: None)


def test_training_is_reproducible():
    df = synthetic_df()
    _, m1 = training_ops.entrainer(df, seed=42)
    _, m2 = training_ops.entrainer(df, seed=42)
    assert m1 == m2


def test_agent_trains_and_publishes_model():
    client = FakeClient()
    state = setup_dataset(client)
    out = run_training(state, client=client)
    assert out["model_uri"].startswith("s3://models/adult_logreg/v1/")
    assert set(out["metrics"]) == {"accuracy", "f1"}
    assert storage.list_keys("models", client=client)


def test_agent_refuses_invalid_hash():
    client = FakeClient()
    state = setup_dataset(client)
    state["dataset_hash"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="hash"):
        run_training(state, client=client)
    assert storage.list_keys("models", client=client) == []