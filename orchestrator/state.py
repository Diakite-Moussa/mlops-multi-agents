from typing import TypedDict

class PipelineState(TypedDict, total=False):
    run_id: str
    status: str            # running | failed | done
    dataset_uri: str
    dataset_hash: str
    model_uri: str
    metrics: dict
    qa_report: dict
    data_report: dict
    errors: list