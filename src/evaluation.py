"""Evaluation: silhouette/elbow for clusters, leave-one-out for recommendation."""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .features import AUDIO_FEATURES


def genre_consistency(recs: pd.DataFrame, seed_df: pd.DataFrame, col: str = "playlist_genre") -> float:
    if col not in recs or col not in seed_df:
        return float("nan")
    seed_genres = set(seed_df[col].dropna())
    if not seed_genres:
        return 0.0
    return recs[col].isin(seed_genres).mean()


def intra_list_diversity(recs: pd.DataFrame) -> float:
    X = recs[AUDIO_FEATURES].values
    if len(X) < 2:
        return 0.0
    sims = cosine_similarity(X)
    iu = np.triu_indices_from(sims, k=1)
    return 1 - sims[iu].mean()


def leave_one_out(
    catalog: pd.DataFrame,
    seed_df: pd.DataFrame,
    k: int = 10,
) -> dict:
    hits = 0
    ranks = []
    for i in seed_df.index:
        held_out = seed_df.loc[[i]]
        remaining = seed_df.drop(index=i)
        if len(remaining) == 0:
            continue
        profile = remaining[AUDIO_FEATURES].mean().values.reshape(1, -1)
        pool = catalog.drop(index=remaining.index, errors="ignore")
        sims = cosine_similarity(pool[AUDIO_FEATURES].values, profile).ravel()
        order = np.argsort(-sims)
        target_pos = pool.index.get_loc(held_out.index[0]) if held_out.index[0] in pool.index else None
        if target_pos is None:
            continue
        rank = int(np.where(order == target_pos)[0][0]) + 1
        ranks.append(rank)
        if rank <= k:
            hits += 1
    n = len(ranks) or 1
    return {
        "hit_rate_at_k": hits / n,
        "mean_rank": float(np.mean(ranks)) if ranks else float("nan"),
        "n": len(ranks),
    }
