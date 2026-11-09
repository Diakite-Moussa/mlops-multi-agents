import pytest


@pytest.fixture(autouse=True)
def fake_data_agent(monkeypatch):
    monkeypatch.setattr("agents.data.agent.process_dataset", lambda *a, **k: {
        "dataset_uri": "s3://datasets/mock/v1.csv", "dataset_hash": "sha256:mock"})
