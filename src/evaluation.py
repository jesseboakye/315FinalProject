"""Evaluation: silhouette/elbow for clusters, leave-one-out for recommendation."""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .features import AUDIO_FEATURES


def collapse_sparse_genres(
    s: pd.Series,
    catalog_genres: pd.Series | None = None,
    min_count: int = 30,
    other: str = "other",
) -> pd.Series:
    """Bucket genres with fewer than min_count tracks (in the catalog) into ``other``."""
    counts = (catalog_genres if catalog_genres is not None else s).value_counts()
    keep = set(counts[counts >= min_count].index)
    return s.where(s.isin(keep), other)


def genre_consistency(
    recs: pd.DataFrame,
    seed_df: pd.DataFrame,
    col: str = "playlist_genre",
    catalog: pd.DataFrame | None = None,
    min_count: int = 30,
) -> float:
    if col not in recs or col not in seed_df:
        return float("nan")
    if catalog is not None and col in catalog:
        ref = catalog[col]
        seed_g = collapse_sparse_genres(seed_df[col], ref, min_count)
        rec_g = collapse_sparse_genres(recs[col], ref, min_count)
    else:
        seed_g, rec_g = seed_df[col], recs[col]
    seed_genres = set(seed_g.dropna())
    if not seed_genres:
        return 0.0
    return rec_g.isin(seed_genres).mean()


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
