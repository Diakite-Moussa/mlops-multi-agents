import io

import pandas as pd

from core import data_ops, storage, versioning
from orchestrator.tracing import traced

MAX_MISSING_RATIO = 0.30   # au-delà, les données sont inutilisables
MIN_ROWS_KEPT = 0.50       # on refuse de supprimer plus de la moitié des lignes


def process_dataset(client=None, raw_bucket="datasets", raw_key="raw/adult.csv") -> dict:
    raw = pd.read_csv(io.BytesIO(storage.download_bytes(raw_bucket, raw_key, client=client)))
    report = data_ops.quality_report(raw)

    if report["n_rows"] == 0:
        raise ValueError("dataset vide")
    if report["missing_ratio_total"] > MAX_MISSING_RATIO:
        raise ValueError(f"trop de valeurs manquantes : {report['missing_ratio_total']:.0%} "
                         f"(seuil {MAX_MISSING_RATIO:.0%})")

    cleaned = data_ops.clean(raw)
    if len(cleaned) < MIN_ROWS_KEPT * report["n_rows"]:
        raise ValueError(f"nettoyage trop destructif : {len(cleaned)}/{report['n_rows']} lignes conservées")

    published = versioning.publish_dataset(
        cleaned, report, raw_uri=storage.make_uri(raw_bucket, raw_key), client=client)
    return {"dataset_uri": published["dataset_uri"],
            "dataset_hash": published["dataset_hash"],
            "data_report": {**report, "rows_after_cleaning": len(cleaned),
                            "version": published["version"], "reused": published["reused"]}}


@traced("data")
def data_node(state):
    return process_dataset()
