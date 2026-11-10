"""Pointeur « modèle en production » stocké dans MinIO (models/production/current.json)."""
import json
from datetime import datetime, timezone

from core import storage

BUCKET = "models"
PROD_KEY = "production/current.json"


def get_production(client=None) -> dict | None:
    if PROD_KEY not in storage.list_keys(BUCKET, "production/", client=client):
        return None
    return json.loads(storage.download_bytes(BUCKET, PROD_KEY, client=client))


def set_production(model_uri: str, client=None) -> dict:
    pointer = {"model_uri": model_uri,
               "promoted_at": datetime.now(timezone.utc).isoformat()}
    storage.upload_bytes(BUCKET, PROD_KEY, json.dumps(pointer, indent=2).encode(),
                         content_type="application/json", client=client)
    return pointer
