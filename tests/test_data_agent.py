import pandas as pd
import pytest

from agents.data.agent import process_dataset
from core import data_ops, storage


class _Obj:
    def __init__(self, name):
        self.object_name = name


class _Resp:
    def __init__(self, data):
        self.data = data

    def read(self):
        return self.data

    def close(self):
        pass

    def release_conn(self):
        pass


class FakeClient:
    def __init__(self):
        self.store = {}

    def put_object(self, bucket, key, data, length, content_type=None):
        self.store[(bucket, key)] = data.read()

    def get_object(self, bucket, key):
        return _Resp(self.store[(bucket, key)])

    def list_objects(self, bucket, prefix="", recursive=True):
        return [_Obj(k) for (b, k) in self.store if b == bucket and k.startswith(prefix)]


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
