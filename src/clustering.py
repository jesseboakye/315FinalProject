"""K-means clustering on normalized audio features for personality archetypes."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from .features import AUDIO_FEATURES


def fit_kmeans(X: np.ndarray, k: int, random_state: int = 42) -> KMeans:
    return KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=random_state).fit(X)


def evaluate_k(
    X: np.ndarray,
    k_range=range(2, 11),
    random_state: int = 42,
) -> dict[int, dict]:
    """Run KMeans across k_range and return inertia, silhouette, and cluster sizes per K."""
    out: dict[int, dict] = {}
    for k in k_range:
        km = fit_kmeans(X, k, random_state)
        labels = km.labels_
        sil = float(silhouette_score(X, labels))
        sizes = np.bincount(labels, minlength=k).tolist()
        out[k] = {"inertia": float(km.inertia_), "silhouette": sil, "sizes": sizes}
    return out


def fit_kmeans_pca(
    X: np.ndarray,
    n_components: int,
    k: int,
    random_state: int = 42,
) -> tuple[PCA, KMeans]:
    pca = PCA(n_components=n_components, random_state=random_state)
    Xp = pca.fit_transform(X)
    km = fit_kmeans(Xp, k, random_state)
    return pca, km


def cluster_profile(
    df: pd.DataFrame,
    labels: np.ndarray,
    features: list[str] = AUDIO_FEATURES,
) -> pd.DataFrame:
    """Mean of each feature per cluster (always on the original feature space)."""
    out = df[features].copy()
    out["cluster"] = labels
    return out.groupby("cluster").mean()
