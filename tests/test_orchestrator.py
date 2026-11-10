from orchestrator.graph import build_graph

def run():
    return build_graph().invoke({"run_id": "test", "status": "running", "errors": []})

def test_pipeline_success(monkeypatch):
    monkeypatch.delenv("FAIL_AT", raising=False)
    assert run()["status"] == "done"

def test_pipeline_stops_on_failure(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("échec simulé dans training")
    monkeypatch.setattr("agents.training.agent.run_training", boom)
    result = run()
    assert result["status"] == "failed"
    assert "model_uri" not in result
    assert "qa_report" not in result   # QA et Release n'ont pas tourné