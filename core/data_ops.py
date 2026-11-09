import hashlib

import numpy as np
import pandas as pd

MISSING_TOKENS = ["?", ""]
RANGES = {"age": (0, 120), "hours-per-week": (0, 168)}


def normalize_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Supprime les espaces et remplace '?' et '' par NaN dans les colonnes texte."""
    out = df.copy()
    for col in out.columns:
        if not pd.api.types.is_numeric_dtype(out[col]):
            out[col] = out[col].astype("object").map(lambda v: v.strip() if isinstance(v, str) else v)
            out[col] = out[col].replace(MISSING_TOKENS, np.nan)
    return out


def quality_report(df: pd.DataFrame, ranges: dict = RANGES) -> dict:
    d = normalize_missing(df)
    n = len(d)
    missing = d.isna().mean()
    out_of_range = {}
    for col, (lo, hi) in ranges.items():
        if col in d.columns:
            s = pd.to_numeric(d[col], errors="coerce")
            out_of_range[col] = int(((s < lo) | (s > hi)).sum())
    total_cells = n * d.shape[1]
    return {
        "n_rows": int(n),
        "n_cols": int(d.shape[1]),
        "duplicates": int(d.duplicated().sum()),
        "missing_ratio_by_col": {c: round(float(v), 4) for c, v in missing.items() if v > 0},
        "missing_ratio_total": round(float(d.isna().sum().sum() / total_cells), 4) if total_cells else 1.0,
        "out_of_range": out_of_range,
    }


def clean(df: pd.DataFrame, ranges: dict = RANGES) -> pd.DataFrame:
    d = normalize_missing(df).drop_duplicates()
    for col, (lo, hi) in ranges.items():
        if col in d.columns:
            s = pd.to_numeric(d[col], errors="coerce")
            d = d[s.isna() | ((s >= lo) & (s <= hi))]
    d = d.copy()
    for col in d.columns:
        if d[col].isna().any():
            if pd.api.types.is_numeric_dtype(d[col]):
                d[col] = d[col].fillna(d[col].median())
            else:
                mode = d[col].mode()
                if len(mode):
                    d[col] = d[col].fillna(mode.iloc[0])
    return d.reset_index(drop=True)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, lineterminator="\n").encode("utf-8")


def dataframe_hash(df: pd.DataFrame) -> str:
    """Empreinte du CSV nettoyé : elle peut être revérifiée sur le fichier stocké."""
    return "sha256:" + hashlib.sha256(to_csv_bytes(df)).hexdigest()
