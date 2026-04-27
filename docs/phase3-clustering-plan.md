# Phase 3 Plan — Clustering & Music Personality Archetypes

## Goal

Pick a final K, fit K-means on the cleaned and MinMax-scaled audio features, label each cluster with a human-readable "music personality" archetype, and persist the trained artifacts so the Streamlit app can predict instantly without refitting on every interaction.

## Inputs

- Cleaned dataframe from `src.preprocessing.load_dataset()` (4,494 tracks)
- 8 normalized audio features from `src.features.AUDIO_FEATURES`
- Constraints from [docs/plan-adjustments.md](plan-adjustments.md) — particularly the PCA experiment requirement and the rule that recommendations stay on original features regardless of clustering input

## Two-track experiment

EDA showed strong correlations (energy ↔ loudness ≈ 0.80) and 6 PCA components capturing ≥ 95% variance. Run two parallel K-means fits and pick the winner by silhouette:

| Track | Input | Notes |
|---|---|---|
| **A** | Original 8 normalized features | Default; clusters interpretable directly from centroid feature values |
| **B** | 6-component PCA representation | Removes redundancy; centroids must be back-projected to feature space for labeling |

For each track, scan `K = 2..10` and record:
- Silhouette score
- Inertia (for the elbow)
- Cluster size distribution (flag any K that produces a degenerate one-cluster-takes-most outcome)

**Decision rule**: pick the (track, K) pair with the highest silhouette, breaking ties in favor of Track A (interpretability) and against Ks that produce a cluster < 2% of the dataset.

## Notebook outline — `notebooks/02_clustering.ipynb`

1. **Setup** — imports, `sys.path`, fixed RNG.
2. **Load + scale** — reuse `src.preprocessing` (no refitting MinMax).
3. **Track A scan** — `K = 2..10`, plot inertia + silhouette curves.
4. **Track B scan** — fit PCA(6), run same scan on the projection.
5. **Select winner** — print final K, track, silhouette, inertia. Justify in markdown.
6. **Fit final model** — use winning config; store the labels back on the dataframe.
7. **Cluster profile heatmap** — mean of original 8 features per cluster (for Track B, compute means on original features grouped by predicted cluster — not from PCA centroids).
8. **Cluster size + genre composition** — bar chart of cluster sizes; top 5 `playlist_genre` per cluster.
9. **PCA(2D) scatter colored by cluster** — visual sanity check.
10. **Draft archetype labels** — derive from centroid profile; record the cluster → label mapping in code.
11. **Persist** — save `MinMaxScaler`, `KMeans` (and `PCA` if Track B wins), and the label map under `artifacts/`.

## Code additions

### `src/clustering.py` (extend)

- `evaluate_k(X, k_range) -> dict[int, dict]` returning `{k: {"inertia": ..., "silhouette": ..., "sizes": [...]}}` — replaces the two existing scan helpers.
- `fit_kmeans_pca(df, n_components, k, random_state)` — fits PCA + KMeans together, returns both.
- `cluster_profile(df, labels, features)` — DataFrame of per-cluster means on the original feature space (works regardless of which track won).

### `src/artifacts.py` (new)

- `save_artifacts(path, scaler, kmeans, label_map, pca=None)` — joblib bundle.
- `load_artifacts(path) -> dict` — used by the Streamlit app.
- `predict_personality(seed_df, artifacts) -> str` — applies scaler (and PCA if present), runs KMeans, returns the label.

### `artifacts/` directory

Already gitignored. Holds the `.joblib` bundle plus a small JSON sidecar with metadata (final K, silhouette, track, training timestamp, feature list) for reproducibility.

## Acceptance criteria

- [ ] Final (track, K) selected with both elbow and silhouette evidence shown in the notebook.
- [ ] No cluster smaller than 2% of the dataset (~90 tracks).
- [ ] Each cluster has a human-readable archetype label backed by its centroid profile, recorded in the notebook **and** persisted in the artifact bundle.
- [ ] `load_artifacts` + `predict_personality` round-trip works on a fresh seed sample in under 1 second.
- [ ] Notebook runs end-to-end on a clean checkout (`nbclient` execution test, same as Phase 2).
- [ ] Cluster archetype labels reviewed by the team before being committed.

## Risks & open questions

- **Imbalanced clusters.** The genre distribution is skewed toward electronic/pop/latin. K-means may produce one mega-cluster of mainstream pop/electronic plus several small ones. Mitigation: enforce the 2%-floor rule above; if it bites, try `MiniBatchKMeans` with `init='k-means++'` and more `n_init` runs, or step K down.
- **Wellness / classical / lofi merging.** EDA suggests these share a clear acoustic/instrumental profile and may collapse into one "calm" cluster. That's acceptable — note it in the report rather than forcing K up to split them.
- **Track B winning.** Adds PCA at predict time and makes centroid interpretation indirect. If Track B's silhouette wins by < 0.02, prefer Track A for the explainability gain. Document the trade-off either way.
- **Random seed sensitivity.** K-means depends on init. Use `n_init=10` (already the default) and lock `random_state=42`. Report silhouette mean ± std across 5 seeds for the final K to confirm stability.
- **Archetype label drift.** Labels are subjective. Draft them in the notebook, review as a team, then freeze in the artifact bundle. Don't re-label without re-running the persist step.

## Out of scope for this phase

- Streamlit integration (Phase 7).
- Soft-cluster GMM personalities (stretch goal).
- Refitting on a subset of features per cluster.

## Definition of done

`02_clustering.ipynb` committed with rendered key plots; `artifacts/personality_v1.joblib` (or equivalent) persisted; `predict_personality` callable from a fresh Python session and producing a sensible label for a hand-picked seed set (e.g., 5 high-energy electronic tracks → a dance/upbeat archetype).
