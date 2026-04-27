"""K-means clustering on normalized audio features for personality archetypes."""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from .features import AUDIO_FEATURES


def fit_kmeans(df: pd.DataFrame, k: int, random_state: int = 42) -> KMeans:
    model = KMeans(n_clusters=k, init="k-means++", n_init=10, random_state=random_state)
    model.fit(df[AUDIO_FEATURES].values)
    return model


def elbow_scan(df: pd.DataFrame, k_range=range(2, 11)) -> dict[int, float]:
    X = df[AUDIO_FEATURES].values
    return {k: fit_kmeans(df, k).inertia_ for k in k_range}


def silhouette_scan(df: pd.DataFrame, k_range=range(2, 11)) -> dict[int, float]:
    X = df[AUDIO_FEATURES].values
    out = {}
    for k in k_range:
        labels = fit_kmeans(df, k).predict(X)
        out[k] = silhouette_score(X, labels)
    return out
