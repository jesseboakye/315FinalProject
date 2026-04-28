# Plan Adjustments

Living delta on top of the original CPTS 315 implementation plan PDF. Captures changes from the peer-feedback pass and from EDA findings in [notebooks/01_eda.ipynb](../notebooks/01_eda.ipynb). The PDF stays the baseline; this file is what's authoritative when they conflict.

## From peer feedback

- **Tech stack:** add **Streamlit** for the interactive Wrapped-style demo (song selection, report pages, charts).
- **Feature set:** unify on the same 8 normalized audio features for clustering and recommendation — `danceability, energy, valence, acousticness, instrumentalness, speechiness, tempo, loudness`. See [src/features.py](../src/features.py).
- **Tempo scaling:** drop the `tempo / 200` shortcut. All numerics — including tempo — go through `MinMaxScaler`.
- **PCA:** stays in EDA / visualization. Recommendation engine uses original normalized features for explainability.
- **Hidden gems:** replace fixed `cosine > 0.9` with a percentile-based rule (top 10–15% most similar tracks).
- **Evaluation:** add **leave-one-out seed recovery** — drop one seed, build profile from the rest, measure rank of the held-out song. Report Hit Rate@10 and mean rank.

## From EDA findings

### Phase 3 — Clustering: PCA experiment is now concrete

EDA confirmed strong correlations (energy ↔ loudness ≈ 0.80; acousticness ↔ energy ≈ -0.76) and that **6 PCA components capture ≥ 95% variance**. Phase 3 will explicitly run two K-means experiments:

1. K-means on the **8 original normalized features**.
2. K-means on a **6-component PCA representation**.

Compare silhouette scores across the same K range; pick the representation that scores higher. Recommendation continues to use original features regardless of which clustering input wins, so cluster labels stay interpretable.

### Phase 3 — Cluster archetype labels are hypotheses, not fixed

EDA's per-genre audio profile suggests four candidate archetypes (calm/instrumental, dance/upbeat, high-intensity, rhythm/flow). These are **starting hypotheses only**. Final K is chosen by elbow + silhouette (likely 5–8), and final labels are derived from centroid feature profiles after K-means runs — not from genres.

### Phase 4 — Mood threshold tuning

Mood-quadrant scatter showed all four quadrants populated, but the low-energy/high-valence region was sparse at the 0.5 split. Replace the 0.5 thresholds in `src/mood.py` with:

- High valence / high energy: **≥ 0.6**
- Low valence: **< 0.35**

This produces more distinct mood labels and matches where the data actually clusters.

### Phase 5 — Hidden gems cutoff is adaptive

Popularity is a continuous distribution, not two clean buckets. Use the **lower of (dataset median popularity, user's average seed popularity)** as the popularity ceiling for hidden gems. This handles two user types:

- Mainstream listener → ceiling is the dataset median, so gems are genuinely less-popular.
- Niche listener → ceiling is their already-low average, so the system doesn't surface mainstream tracks they'd consider too popular.

Combined with the top-percentile similarity filter, gems are: high similarity AND popularity below `min(median, user_avg)`.

### Phase 7 — Genre column hidden from per-track displays

The Kaggle dataset's `playlist_genre` column tags each track with the genre of the *Spotify playlist it was scraped from*, not the song's own genre. The same song appears under different labels depending on the source playlist. Concrete cases surfaced during the demo:

- Lil Baby's *Freestyle* tagged `arabic` — scraped from a playlist named "Arab X".
- Gunna's *fukumean* tagged `gaming` — scraped from "Top Gaming Tracks", a playlist that also contains Taylor Swift, Charli xcx, and Travis Scott.

We explored four corrections (album-majority, artist-majority, hybrid, conservative-agreement). All have failure modes: album-majority misses single-track albums (75 fixes, leaves *Freestyle* wrong); artist-majority overrides correctly-labeled tracks (171 fixes but regresses *HIM ALL ALONG* from `hip-hop` to `gaming`); none fix artists like Asake whose entire catalog representation came from the wrong source playlists.

**Decision: hide the genre column from per-track displays in the Streamlit demo.** Cleanest "do less" answer. The recommendations and hidden-gems tables show **Track · Artist · Similarity** only; the song-picker search results show **Track · Artist**. The audio-feature-driven engine (clustering, recs, gems) was never affected by the noise — this is purely a display decision.

What stays: the aggregate genre summary on Slide 1 ("Your Music in Numbers") still shows top genre and the genre bar chart over the user's selection. Aggregate label noise on a 3–10 song selection is small and still informative for the user.

What this means for the report: explicitly call out the dataset limitation. Audio-feature recs are acoustically correct; the labels in the source data are not reliable enough to display per-track without misleading viewers.

### Phase 6 — Sparse genre handling for evaluation

Genre distribution is heavily skewed: top genres (electronic, pop, latin, hip-hop, ambient, rock, lofi) have 300–560 tracks each, while sparse genres (disco, country, mandopop, soca) have only a handful. For the **genre consistency** metric, group all sparse genres (e.g., < 30 tracks) into an `"other"` bucket before computing match rate — otherwise the metric is dominated by tiny-sample noise.

Cluster evaluation and recommendation are unaffected; this is purely an evaluation-side adjustment.

## Open questions

- Final K for K-means — pending elbow + silhouette scan in `02_clustering.ipynb`.
- Whether 6-component PCA actually wins on silhouette vs. original 8 features.
- Exact sparse-genre threshold (30 tracks is a starting point; revisit after seeing genre-consistency variance).
