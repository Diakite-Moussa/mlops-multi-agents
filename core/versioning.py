import json
import os
import re
from datetime import datetime, timezone

from core import storage
from core.data_ops import to_csv_bytes


def publish_dataset(df, report, name="adult", bucket="datasets", raw_uri=None, client=None) -> dict:
    data = to_csv_bytes(df)
    digest = storage.sha256_bytes(data)
    short = digest.split(":")[1][:8]
    csvs = [k for k in storage.list_keys(bucket, f"{name}/", client=client) if k.endswith(".csv")]

    for key in csvs:
        if key.endswith(f"_{short}.csv"):
            version = int(re.search(r"/v(\d+)_", key).group(1))
            return {"dataset_uri": storage.make_uri(bucket, key), "dataset_hash": digest,
                    "version": version, "reused": True}

    version = len(csvs) + 1
    key = f"{name}/v{version}_{short}.csv"
    uri = storage.upload_bytes(bucket, key, data, content_type="text/csv", client=client)
    metadata = {
        "dataset_uri": uri, "dataset_hash": digest, "version": version,
        "source": raw_uri, "n_rows": len(df), "quality_report": report,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "author": os.getenv("PIPELINE_AUTHOR", "unknown"),
    }
    storage.upload_bytes(bucket, key.replace(".csv", ".metadata.json"),
                         json.dumps(metadata, ensure_ascii=False, indent=2).encode(),
                         content_type="application/json", client=client)
    return {"dataset_uri": uri, "dataset_hash": digest, "version": version, "reused": False}
