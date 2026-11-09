import pandas as pd

from core.data_ops import clean, dataframe_hash, quality_report


def sample():
    return pd.DataFrame({
        "age": [25, 25, 40, 200, 30],
        "workclass": ["Private", "Private", "?", "Gov", "Private"],
        "hours-per-week": [40, 40, 50, 30, None],
    })


def test_quality_report():
    r = quality_report(sample())
    assert r["n_rows"] == 5
    assert r["duplicates"] == 1
    assert r["missing_ratio_by_col"]["workclass"] == 0.2
    assert r["out_of_range"]["age"] == 1


def test_clean():
    c = clean(sample())
    assert len(c) == 3                      # 1 doublon et 1 âge aberrant retirés
    assert not c.isna().any().any()
    assert "?" not in c["workclass"].values


def test_hash_is_deterministic():
    a = clean(sample())
    b = clean(sample())
    assert dataframe_hash(a) == dataframe_hash(b)
    b.loc[0, "age"] = 99
    assert dataframe_hash(a) != dataframe_hash(b)
