import io
import os

import joblib
import mlflow
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from core import storage

TARGET = "class"
POSITIVE = ">50K"
SEED = 42
TEST_SIZE = 0.2
MODEL_NAME = "adult_logreg"


def load_dataset(uri: str, expected_hash: str, client=None) -> pd.DataFrame:
    """Télécharge le CSV et refuse tout fichier dont l'empreinte ne correspond pas."""
    bucket, key = storage.parse_uri(uri)
    data = storage.download_bytes(bucket, key, client=client)
    actual = storage.sha256_bytes(data)
    if actual != expected_hash:
        raise ValueError(f"hash invalide : attendu {expected_hash[:19]}..., obtenu {actual[:19]}...")
    return pd.read_csv(io.BytesIO(data))


def split(df: pd.DataFrame, seed: int = SEED):
    y = (df[TARGET].astype(str).str.strip().str.rstrip(".") == POSITIVE).astype(int)
    X = df.drop(columns=[TARGET])
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=seed, stratify=y)


def build_pipeline(X: pd.DataFrame, seed: int = SEED) -> Pipeline:
    num = X.select_dtypes(include="number").columns.tolist()
    cat = [c for c in X.columns if c not in num]
    pre = ColumnTransformer([
        ("num", StandardScaler(), num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat),
    ])
    return Pipeline([("pre", pre), ("clf", LogisticRegression(max_iter=1000, random_state=seed))])


def evaluer(model, X_te, y_te) -> dict:
    pred = model.predict(X_te)
    return {"accuracy": round(float(accuracy_score(y_te, pred)), 4),
            "f1": round(float(f1_score(y_te, pred)), 4)}


def entrainer(df: pd.DataFrame, seed: int = SEED):
    X_tr, X_te, y_tr, y_te = split(df, seed)
    model = build_pipeline(X_tr, seed)
    model.fit(X_tr, y_tr)
    return model, evaluer(model, X_te, y_te)


def publish_model(model, name: str = MODEL_NAME, bucket: str = "models", client=None) -> str:
    existing = [k for k in storage.list_keys(bucket, f"{name}/", client=client)
                if k.endswith("/model.pkl")]
    key = f"{name}/v{len(existing) + 1}/model.pkl"
    buf = io.BytesIO()
    joblib.dump(model, buf)
    return storage.upload_bytes(bucket, key, buf.getvalue(), client=client)


def log_run(params: dict, metrics: dict, dataset_uri: str, dataset_hash: str,
            model_uri: str, run_name: str = "training") -> None:
    mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    mlflow.set_experiment("adult-income")
    with mlflow.start_run(run_name=run_name):
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.set_tags({"dataset_uri": dataset_uri, "dataset_hash": dataset_hash,
                         "model_uri": model_uri})