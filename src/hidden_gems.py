"""Hidden gems: top-percentile-similar tracks below the user's average popularity."""

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
) -> pd.DataFrame:
    profile = user_profile(seed_df)
    sims = cosine_similarity(catalog[AUDIO_FEATURES].values, profile).ravel()
    out = catalog.copy()
    out["similarity"] = sims
    out = out[~out.index.isin(seed_df.index)]

    cutoff = np.quantile(out["similarity"], 1 - top_pct)
    candidates = out[out["similarity"] >= cutoff]

    seed_pop = seed_df["track_popularity"].mean() if "track_popularity" in seed_df else 50
    candidates = candidates[candidates["track_popularity"] < seed_pop]
    return candidates.nlargest(n, "similarity")
