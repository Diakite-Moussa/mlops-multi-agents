import numpy as np
import pandas as pd
import pytest

from agents.qa.agent import run_qa
from core import data_ops, qa_ops, registry, storage, training_ops
from tests.fakes import FakeClient


def synthetic_df(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    age = rng.integers(18, 70, n)
    hours = rng.integers(20, 60, n)
    sex = rng.choice(["Male", "Female"], n)
    race = rng.choice(["White", "Black"], n)
    score = age / 70 + hours / 60 + (sex == "Male") * 0.3 + rng.normal(0, 0.3, n)
    return pd.DataFrame({"age": age, "hours-per-week": hours, "sex": sex, "race": race,
                         "class": np.where(score > 1.3, ">50K", "<=50K")})


def bad_model(df):
    shuffled = df.copy()
    shuffled["class"] = np.random.default_rng(1).permutation(shuffled["class"].values)
    return training_ops.entrainer(shuffled)[0]


def test_demographic_parity_gap():
    assert qa_ops.demographic_parity_gap([1, 1, 0, 0], ["a", "a", "b", "b"]) == 1.0
    assert qa_ops.demographic_parity_gap([1, 0, 1, 0], ["a", "a", "b", "b"]) == 0.0


def test_matches_fairlearn():
    fairlearn = pytest.importorskip("fairlearn.metrics")
    pred = np.array([1, 0, 1, 1, 0, 0, 1, 0])
    groups = np.array(list("aaaabbbb"))
    expected = fairlearn.demographic_parity_difference(pred, pred, sensitive_features=groups)
    assert qa_ops.demographic_parity_gap(pred, groups) == pytest.approx(expected)


def test_report_without_production():
    df = synthetic_df()
    model, _ = training_ops.entrainer(df)
    r = qa_ops.build_report(model, df)
    assert r["regression_vs_prod"] is None and r["prod_accuracy"] is None
    assert set(r["fairness_by_attr"]) == {"sex", "race"}
    assert r["fairness_gap"] == max(r["fairness_by_attr"].values())
    assert r["accuracy"] > 0.7


def test_regression_detected_against_production():
    df = synthetic_df()
    good, _ = training_ops.entrainer(df)
    r = qa_ops.build_report(bad_model(df), df, production=good)
    assert r["regression_vs_prod"] > 0.1


def test_report_is_deterministic():
    df = synthetic_df()
    model, _ = training_ops.entrainer(df)
    assert qa_ops.build_report(model, df) == qa_ops.build_report(model, df)


def test_registry_roundtrip():
    client = FakeClient()
    assert registry.get_production(client=client) is None
    registry.set_production("s3://models/adult_logreg/v1/model.pkl", client=client)
    assert registry.get_production(client=client)["model_uri"] == "s3://models/adult_logreg/v1/model.pkl"


def setup_run(client, with_production):
    df = synthetic_df()
    data = data_ops.to_csv_bytes(df)
    uri = storage.upload_bytes("datasets", "adult/v1_t.csv", data, client=client)
    good, _ = training_ops.entrainer(df)
    state = {"dataset_uri": uri, "dataset_hash": storage.sha256_bytes(data),
             "model_uri": training_ops.publish_model(good, client=client)}
    if with_production:
        registry.set_production(training_ops.publish_model(good, client=client), client=client)
    return state


def test_agent_first_release():
    client = FakeClient()
    out = run_qa(setup_run(client, with_production=False), client=client)
    assert out["qa_report"]["regression_vs_prod"] is None


def test_agent_compares_with_production():
    client = FakeClient()
    out = run_qa(setup_run(client, with_production=True), client=client)
    assert out["qa_report"]["regression_vs_prod"] == 0.0
