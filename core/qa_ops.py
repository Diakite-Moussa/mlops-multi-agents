"""Fonctions de contrôle qualité d'un modèle : sans LangGraph ni MinIO (réutilisables par la baseline)."""
import io

import joblib
import numpy as np
import pandas as pd

from core import storage, training_ops

SENSITIVE = ["sex", "race"]


def load_model(uri: str, client=None):
    bucket, key = storage.parse_uri(uri)
    return joblib.load(io.BytesIO(storage.download_bytes(bucket, key, client=client)))


def holdout(df: pd.DataFrame, seed: int = training_ops.SEED):
    """Rejoue exactement le split de l'entraînement : mêmes lignes de test."""
    _, X_te, _, y_te = training_ops.split(df, seed)
    return X_te, y_te


def demographic_parity_gap(pred, groups) -> float:
    """Écart max entre les taux de prédictions positives des groupes
    (même définition que fairlearn.metrics.demographic_parity_difference)."""
    rates = pd.Series(np.asarray(pred)).groupby(np.asarray(groups)).mean()
    return float(rates.max() - rates.min())


def robustness_drop(model, X_te, y_te, seed: int = training_ops.SEED, noise: float = 0.05) -> float:
    """Perte d'accuracy quand on ajoute un bruit gaussien (5 % de l'écart-type) aux colonnes numériques."""
    rng = np.random.default_rng(seed)
    X_noisy = X_te.copy()
    for col in X_noisy.select_dtypes(include="number").columns:
        std = float(X_noisy[col].std() or 0.0)
        X_noisy[col] = X_noisy[col] + rng.normal(0.0, noise * std, len(X_noisy))
    base = training_ops.evaluer(model, X_te, y_te)["accuracy"]
    noisy = training_ops.evaluer(model, X_noisy, y_te)["accuracy"]
    return round(base - noisy, 4)


def evaluate(model, X_te, y_te, sensitive=SENSITIVE) -> dict:
    metrics = training_ops.evaluer(model, X_te, y_te)
    pred = model.predict(X_te)
    by_attr = {c: round(demographic_parity_gap(pred, X_te[c]), 4)
               for c in sensitive if c in X_te.columns}
    return {**metrics,
            "fairness_by_attr": by_attr,
            "fairness_gap": max(by_attr.values(), default=0.0),
            "robustness_drop": robustness_drop(model, X_te, y_te)}


def build_report(candidate, df: pd.DataFrame, production=None, seed: int = training_ops.SEED) -> dict:
    X_te, y_te = holdout(df, seed)
    report = evaluate(candidate, X_te, y_te)
    prod_acc = regression = None
    if production is not None:
        prod_acc = training_ops.evaluer(production, X_te, y_te)["accuracy"]
        regression = round(prod_acc - report["accuracy"], 4)   # > 0 : le candidat est moins bon
    return {**report, "prod_accuracy": prod_acc, "regression_vs_prod": regression}
