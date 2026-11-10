import pytest


@pytest.fixture(autouse=True)
def fake_data_agent(monkeypatch):
    monkeypatch.setattr("agents.data.agent.process_dataset", lambda *a, **k: {
        "dataset_uri": "s3://datasets/mock/v1.csv", "dataset_hash": "sha256:mock"})


@pytest.fixture(autouse=True)
def fake_training_agent(monkeypatch):
    monkeypatch.setattr("agents.training.agent.run_training", lambda *a, **k: {
        "model_uri": "s3://models/mock/model.pkl", "metrics": {"accuracy": 0.9, "f1": 0.7}})


GOOD_REPORT = {"accuracy": 0.86, "f1": 0.68, "prod_accuracy": None, "regression_vs_prod": None,
               "fairness_gap": 0.12, "fairness_by_attr": {"sex": 0.12}, "robustness_drop": 0.01}


@pytest.fixture(autouse=True)
def fake_qa_agent(monkeypatch):
    monkeypatch.setattr("agents.qa.agent.run_qa", lambda *a, **k: {"qa_report": dict(GOOD_REPORT)})
