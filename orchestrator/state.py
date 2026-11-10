from typing import TypedDict

class PipelineState(TypedDict, total=False):
    run_id: str
    status: str            # running | failed | rejected | done
    dataset_uri: str
    dataset_hash: str
    model_uri: str
    metrics: dict
    qa_report: dict
    data_report: dict
    gate_decision: dict
    approved: bool
    errors: list
