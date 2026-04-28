"""Hidden gems: top-percentile-similar tracks below an adaptive popularity ceiling."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .features import AUDIO_FEATURES
from .recommend import user_profile


def hidden_gems(
    catalog: pd.DataFrame,
    seed_df: pd.DataFrame,
    top_pct: float = 0.10,
    n: int = 10,
    exclude: Iterable | None = None,
) -> pd.DataFrame:
    """Top-percentile-similar tracks below min(catalog median, user avg seed popularity).

    `exclude` accepts catalog DataFrame indices to remove from the candidate pool —
    use this to keep gems disjoint from the main recommendation list.
    """
    profile = user_profile(seed_df)
    sims = cosine_similarity(catalog[AUDIO_FEATURES].values, profile).ravel()
    out = catalog.copy()
    out["similarity"] = sims

    drop = set(seed_df.index)
    if exclude is not None:
        drop |= set(exclude)
    out = out[~out.index.isin(drop)]

    cutoff = np.quantile(out["similarity"], 1 - top_pct)
    candidates = out[out["similarity"] >= cutoff]

    if "track_popularity" in catalog and "track_popularity" in seed_df:
        ceiling = min(catalog["track_popularity"].median(), seed_df["track_popularity"].mean())
        candidates = candidates[candidates["track_popularity"] < ceiling]
    return candidates.nlargest(n, "similarity")
