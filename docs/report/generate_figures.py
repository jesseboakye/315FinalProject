"""Generate all report figures at print-quality resolution.

Run: python docs/report/generate_figures.py
Output: docs/report/figures/*.png
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from src.artifacts import ARTIFACTS_DIR, load_artifacts
from src.clustering import evaluate_k, fit_kmeans
from src.evaluation import (
    genre_consistency,
    intra_list_diversity,
    leave_one_out,
)
from src.features import AUDIO_FEATURES
from src.preprocessing import load_dataset, scale_features
from src.recommend import recommend

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(parents=True, exist_ok=True)
DPI = 200
sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "figure.dpi": DPI, "savefig.dpi": DPI, "savefig.bbox": "tight"})

print("loading dataset…")
df = load_dataset()
scaled, _ = scale_features(df)
X = scaled[AUDIO_FEATURES].values
RNG = 42

# ────────────────────────────── EDA ──────────────────────────────
print("[1/14] feature distributions")
fig, axes = plt.subplots(2, 4, figsize=(13, 6))
for ax, feat in zip(axes.flat, AUDIO_FEATURES):
    sns.histplot(df[feat], ax=ax, bins=40, kde=True, color="#4C78A8")
    ax.set_title(feat)
fig.suptitle("Audio feature distributions (raw)", y=1.02, fontsize=13)
fig.tight_layout()
fig.savefig(OUT / "feature_distributions.png")
plt.close(fig)

print("[2/14] correlation heatmap")
fig, ax = plt.subplots(figsize=(8, 6.5))
sns.heatmap(df[AUDIO_FEATURES].corr(), annot=True, cmap="coolwarm", center=0,
            fmt=".2f", ax=ax, vmin=-1, vmax=1, square=True, cbar_kws={"shrink": 0.7})
ax.set_title("Audio feature correlations")
fig.tight_layout()
fig.savefig(OUT / "correlation_heatmap.png")
plt.close(fig)

print("[3/14] popularity distribution")
from src.preprocessing import HIGH_POP, LOW_POP
high = pd.read_csv(HIGH_POP).assign(source="high_popularity")
low = pd.read_csv(LOW_POP).assign(source="low_popularity")
tagged = pd.concat([high, low], ignore_index=True)
fig, ax = plt.subplots(figsize=(9, 4))
sns.histplot(data=tagged, x="track_popularity", hue="source", bins=50,
             element="step", common_norm=False, ax=ax)
ax.axvline(df["track_popularity"].median(), color="black", ls="--", label=f"median={df['track_popularity'].median():.0f}")
ax.set_title("track_popularity by source file")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "popularity_distribution.png")
plt.close(fig)

print("[4/14] genre balance")
genre_counts = df["playlist_genre"].value_counts()
fig, ax = plt.subplots(figsize=(11, 4.5))
genre_counts.plot.bar(ax=ax, color="#54A24B")
ax.set_title("Tracks per playlist_genre")
ax.set_ylabel("count")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
fig.tight_layout()
fig.savefig(OUT / "genre_balance.png")
plt.close(fig)

print("[5/14] genre profile heatmap")
profile_by_genre = scaled.groupby("playlist_genre")[AUDIO_FEATURES].mean().sort_index()
fig, ax = plt.subplots(figsize=(10, 7))
sns.heatmap(profile_by_genre, annot=True, fmt=".2f", cmap="viridis", ax=ax, cbar_kws={"shrink": 0.6})
ax.set_title("Mean audio features by genre (MinMax-scaled)")
fig.tight_layout()
fig.savefig(OUT / "genre_profile_heatmap.png")
plt.close(fig)

print("[6/14] mood quadrants")
sample = df.sample(min(1500, len(df)), random_state=RNG)
fig, ax = plt.subplots(figsize=(8, 7))
sns.scatterplot(data=sample, x="valence", y="energy", hue="playlist_genre",
                alpha=0.65, s=14, ax=ax, palette="tab20")
ax.axvline(0.6, color="gray", lw=0.8, ls="--")
ax.axvline(0.35, color="gray", lw=0.8, ls="--")
ax.axhline(0.6, color="gray", lw=0.8, ls="--")
ax.set_title("Mood space: valence × energy (thresholds 0.35, 0.6)")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7, ncol=1)
fig.tight_layout()
fig.savefig(OUT / "mood_quadrants.png")
plt.close(fig)

print("[7/14] PCA 2D + variance")
pca2 = PCA(n_components=2, random_state=RNG).fit(X)
coords = pca2.transform(X)
plot_df = pd.DataFrame(coords, columns=["pc1", "pc2"])
plot_df["genre"] = scaled["playlist_genre"].values
plot_sample = plot_df.sample(min(1500, len(plot_df)), random_state=RNG)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.scatterplot(data=plot_sample, x="pc1", y="pc2", hue="genre",
                palette="tab20", alpha=0.65, s=14, ax=axes[0])
axes[0].set_title(f"PCA(2D) — explained variance {pca2.explained_variance_ratio_.sum():.1%}")
axes[0].legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7)

pca_full = PCA(random_state=RNG).fit(X)
cum = np.cumsum(pca_full.explained_variance_ratio_)
axes[1].plot(np.arange(1, len(cum) + 1), cum, marker="o", color="#4C78A8")
axes[1].axhline(0.95, color="red", ls="--", label="95%")
axes[1].set_xlabel("# components")
axes[1].set_ylabel("cumulative variance")
axes[1].set_title("PCA cumulative explained variance")
axes[1].legend()
fig.tight_layout()
fig.savefig(OUT / "pca_2d_and_variance.png")
plt.close(fig)

# ────────────────────────────── Clustering ──────────────────────────────
print("[8/14] K-means scans (Track A and B)")
results_a = evaluate_k(X, range(2, 11), random_state=RNG)
X_pca6 = PCA(n_components=6, random_state=RNG).fit_transform(X)
results_b = evaluate_k(X_pca6, range(2, 11), random_state=RNG)
ks = list(range(2, 11))
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
axes[0].plot(ks, [results_a[k]["inertia"] for k in ks], marker="o", label="Track A (8 features)")
axes[0].plot(ks, [results_b[k]["inertia"] for k in ks], marker="s", label="Track B (PCA-6)")
axes[0].set_title("K-means inertia (elbow)"); axes[0].set_xlabel("K"); axes[0].set_ylabel("inertia"); axes[0].legend()
axes[1].plot(ks, [results_a[k]["silhouette"] for k in ks], marker="o", label="Track A (8 features)")
axes[1].plot(ks, [results_b[k]["silhouette"] for k in ks], marker="s", label="Track B (PCA-6)")
axes[1].axvspan(5, 8, alpha=0.15, color="green", label="target K range")
axes[1].set_title("K-means silhouette score"); axes[1].set_xlabel("K"); axes[1].set_ylabel("silhouette"); axes[1].legend()
fig.tight_layout()
fig.savefig(OUT / "kmeans_elbow_silhouette.png")
plt.close(fig)

print("[9/14] cluster profile heatmap")
artifacts = load_artifacts(ARTIFACTS_DIR / "personality_v1.joblib")
km = artifacts["kmeans"]
labels = km.predict(X)
profile_clusters = pd.DataFrame(km.cluster_centers_, columns=AUDIO_FEATURES)
profile_clusters.index = [f"{c}: {artifacts['label_map'][c]}" for c in range(len(profile_clusters))]
fig, ax = plt.subplots(figsize=(11, 4.5))
sns.heatmap(profile_clusters, annot=True, fmt=".2f", cmap="viridis", ax=ax)
ax.set_title("K=6 cluster centroids — mean MinMax features")
fig.tight_layout()
fig.savefig(OUT / "cluster_profile.png")
plt.close(fig)

print("[10/14] cluster PCA scatter")
plot_df["cluster"] = labels
plot_df["archetype"] = [artifacts["label_map"][c] for c in labels]
plot_sample_c = plot_df.sample(min(1500, len(plot_df)), random_state=RNG)
fig, ax = plt.subplots(figsize=(10, 7))
sns.scatterplot(data=plot_sample_c, x="pc1", y="pc2", hue="archetype",
                palette="tab10", alpha=0.7, s=18, ax=ax)
ax.set_title("Clusters in PCA(2D) projection")
ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8, title="Archetype")
fig.tight_layout()
fig.savefig(OUT / "cluster_pca.png")
plt.close(fig)

print("[11/14] cluster sizes")
sizes = pd.Series(labels).map(artifacts["label_map"]).value_counts()
fig, ax = plt.subplots(figsize=(10, 4))
sizes.plot.bar(ax=ax, color="#4C78A8")
ax.set_title("Tracks per personality archetype")
ax.set_ylabel("# tracks")
ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")
fig.tight_layout()
fig.savefig(OUT / "cluster_sizes.png")
plt.close(fig)

# ────────────────────────────── Evaluation ──────────────────────────────
print("[12/14] LOO Hit@K curve")
rng = np.random.default_rng(RNG)
counts = scaled["playlist_genre"].value_counts()
valid_genres = counts[counts >= 5].index.tolist()
genre_seeds = []
for _ in range(200):
    g = str(rng.choice(valid_genres))
    pool = scaled[scaled["playlist_genre"] == g]
    sel = rng.choice(pool.index.to_numpy(), size=5, replace=False)
    genre_seeds.append(scaled.loc[sel])
random_seeds = []
for _ in range(200):
    sel = rng.choice(scaled.index.to_numpy(), size=5, replace=False)
    random_seeds.append(scaled.loc[sel])

def collect_ranks(seeds, metric="cosine"):
    all_ranks = []
    for seed in seeds:
        loo = leave_one_out(scaled, seed, k=10, metric=metric)
        all_ranks.extend(loo["ranks"])
    return np.array(all_ranks)

ranks_random = collect_ranks(random_seeds)
ranks_genre = collect_ranks(genre_seeds)

k_curve = np.array([1, 5, 10, 20, 50, 100, 200, 500])
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(k_curve, [(ranks_random <= k).mean() for k in k_curve], marker="o", label="random seeds")
ax.plot(k_curve, [(ranks_genre <= k).mean() for k in k_curve], marker="s", label="genre-coherent seeds")
ax.plot(k_curve, k_curve / len(scaled), ls="--", color="gray", label="random baseline")
ax.set_xscale("log"); ax.set_xlabel("K (log)"); ax.set_ylabel("Hit Rate @ K")
ax.set_title("Leave-one-out Hit Rate @ K (200 simulated users × 5 seeds each)")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "loo_hitrate.png")
plt.close(fig)

print("[13/14] alpha sweep")
alphas = [1.0, 0.95, 0.85, 0.7, 0.5]
sweep_random, sweep_genre = [], []
for a in alphas:
    gc_r = [genre_consistency(recommend(scaled, s, n=10, alpha=a), s, catalog=scaled) for s in random_seeds]
    gc_g = [genre_consistency(recommend(scaled, s, n=10, alpha=a), s, catalog=scaled) for s in genre_seeds]
    sweep_random.append(np.mean(gc_r))
    sweep_genre.append(np.mean(gc_g))
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(alphas, sweep_random, marker="o", label="random seeds")
ax.plot(alphas, sweep_genre, marker="s", label="genre-coherent seeds")
ax.invert_xaxis()
ax.set_xlabel(r"$\alpha$ (similarity weight; $1-\alpha$ is popularity weight)")
ax.set_ylabel("mean genre consistency")
ax.set_title(r"Genre consistency vs $\alpha$ — popularity-blend trade-off")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "alpha_sweep.png")
plt.close(fig)

print("[14/14] cosine vs euclidean")
ranks_cos = collect_ranks(genre_seeds, "cosine")
ranks_euc = collect_ranks(genre_seeds, "euclidean")
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(k_curve, [(ranks_cos <= k).mean() for k in k_curve], marker="o", label="cosine")
ax.plot(k_curve, [(ranks_euc <= k).mean() for k in k_curve], marker="s", label="euclidean")
ax.plot(k_curve, k_curve / len(scaled), ls="--", color="gray", label="random baseline")
ax.set_xscale("log"); ax.set_xlabel("K (log)"); ax.set_ylabel("Hit Rate @ K")
ax.set_title("Cosine vs Euclidean — LOO Hit Rate @ K (genre-coherent seeds)")
ax.legend()
fig.tight_layout()
fig.savefig(OUT / "metric_comparison.png")
plt.close(fig)

print(f"\nDone. {len(list(OUT.glob('*.png')))} figures written to {OUT}")
