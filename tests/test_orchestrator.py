from orchestrator.graph import run_pipeline
from tests.conftest import GOOD_REPORT


def test_pipeline_success_after_human_approval():
    result = run_pipeline(approver=lambda payload: True)
    assert result["status"] == "done"
    assert result["approved"] is True
    assert result["gate_decision"]["decision"] == "needs_human"


def test_pipeline_waits_for_human_without_approver():
    result = run_pipeline()
    assert "__interrupt__" in result
    assert result["status"] == "running"      # Release n'a pas tourné


def test_human_refusal_stops_before_release():
    result = run_pipeline(approver=lambda payload: False)
    assert result["status"] == "rejected"
    assert result["approved"] is False


def test_gate_rejection_never_asks_human(monkeypatch):
    bad = dict(GOOD_REPORT, accuracy=0.5)
    monkeypatch.setattr("agents.qa.agent.run_qa", lambda *a, **k: {"qa_report": bad})
    asked = []
    result = run_pipeline(approver=lambda payload: asked.append(1) or True)
    assert result["status"] == "rejected"
    assert asked == []
    assert "gate:" in result["errors"][0]


def test_pipeline_stops_on_agent_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("échec simulé dans training")
    monkeypatch.setattr("agents.training.agent.run_training", boom)
    result = run_pipeline(approver=lambda payload: True)
    assert result["status"] == "failed"
    assert "model_uri" not in result
    assert "qa_report" not in result
