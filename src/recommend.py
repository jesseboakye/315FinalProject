"""Cosine-similarity recommendation against the user's average feature vector."""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .features import AUDIO_FEATURES


def user_profile(seed_df: pd.DataFrame) -> np.ndarray:
    return seed_df[AUDIO_FEATURES].mean(axis=0).values.reshape(1, -1)


def recommend(
    catalog: pd.DataFrame,
    seed_df: pd.DataFrame,
    n: int = 10,
    alpha: float = 0.85,
) -> pd.DataFrame:
    profile = user_profile(seed_df)
    sims = cosine_similarity(catalog[AUDIO_FEATURES].values, profile).ravel()
    pop = catalog["track_popularity"].values / 100.0 if "track_popularity" in catalog else np.zeros(len(catalog))
    score = alpha * sims + (1 - alpha) * pop
    out = catalog.copy()
    out["similarity"] = sims
    out["score"] = score
    out = out[~out.index.isin(seed_df.index)]
    return out.nlargest(n, "score")
