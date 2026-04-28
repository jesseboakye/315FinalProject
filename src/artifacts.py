"""Persist and load the clustering pipeline (scaler + KMeans + optional PCA + label map)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler

from .features import AUDIO_FEATURES

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


def save_artifacts(
    path: Path | str,
    scaler: MinMaxScaler,
    kmeans: KMeans,
    label_map: dict[int, str],
    pca: PCA | None = None,
    features: list[str] = AUDIO_FEATURES,
    metadata: dict[str, Any] | None = None,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "scaler": scaler,
        "kmeans": kmeans,
        "pca": pca,
        "label_map": {int(k): str(v) for k, v in label_map.items()},
        "features": list(features),
        "metadata": {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            **(metadata or {}),
        },
    }
    joblib.dump(bundle, path)
    return path


def load_artifacts(path: Path | str) -> dict:
    return joblib.load(path)


def _transform(seed_df: pd.DataFrame, artifacts: dict) -> np.ndarray:
    X = artifacts["scaler"].transform(seed_df[artifacts["features"]])
    if artifacts.get("pca") is not None:
        X = artifacts["pca"].transform(X)
    return np.asarray(X)


def predict_personality(seed_df: pd.DataFrame, artifacts: dict) -> str:
    """Map a seed selection (raw rows from the catalog) to an archetype label."""
    X = _transform(seed_df, artifacts)
    profile = X.mean(axis=0).reshape(1, -1)
    cluster = int(artifacts["kmeans"].predict(profile)[0])
    return artifacts["label_map"][cluster]


def predict_clusters(seed_df: pd.DataFrame, artifacts: dict) -> np.ndarray:
    """Per-track cluster assignments for a seed DataFrame."""
    X = _transform(seed_df, artifacts)
    return artifacts["kmeans"].predict(X)
