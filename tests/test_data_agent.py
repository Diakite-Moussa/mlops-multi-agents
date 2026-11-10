import pandas as pd
import pytest

from agents.data.agent import process_dataset
from core import data_ops, storage
from tests.fakes import FakeClient


def put_raw(client, df):
    storage.upload_bytes("datasets", "raw/adult.csv", data_ops.to_csv_bytes(df), client=client)


def good_raw():
    return pd.DataFrame({
        "age": [25, 25, 40, 35, 30, 45, 50, 28, 33, 41],
        "workclass": ["Private", "Private", "?", "Gov", "Private", "Gov", "Private", "Private", "Gov", "Private"],
        "hours-per-week": [40, 40, 50, 30, 35, 40, 45, 38, 42, 40],
    })


def test_agent_versions_then_reuses():
    client = FakeClient()
    put_raw(client, good_raw())
    r1 = process_dataset(client=client)
    r2 = process_dataset(client=client)
    assert r1["dataset_hash"] == r2["dataset_hash"]
    assert r1["data_report"]["reused"] is False and r2["data_report"]["reused"] is True
    keys = storage.list_keys("datasets", "adult/", client=client)
    assert len([k for k in keys if k.endswith(".csv")]) == 1
    assert len([k for k in keys if k.endswith(".metadata.json")]) == 1


def test_agent_rejects_unusable_data():
    client = FakeClient()
    put_raw(client, pd.DataFrame({"a": ["?"] * 10, "b": ["?"] * 10}))
    with pytest.raises(ValueError, match="manquantes"):
        process_dataset(client=client)
