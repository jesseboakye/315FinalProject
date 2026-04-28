"""Music Wrapped — interactive Streamlit demo. Run: streamlit run app/streamlit_app.py"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.artifacts import ARTIFACTS_DIR, load_artifacts, predict_personality
from src.features import AUDIO_FEATURES
from src.hidden_gems import hidden_gems
from src.mood import classify_mood, profile_mood
from src.preprocessing import load_dataset, scale_features
from src.recommend import recommend

from app.copy import (
    ARCHETYPE_DESCRIPTIONS,
    ARCHETYPE_FALLBACK,
    MOOD_DESCRIPTIONS,
    MOOD_FALLBACK,
)

ARTIFACT_PATH = ARTIFACTS_DIR / "personality_v1.joblib"
MIN_SEEDS = 3
MAX_SEEDS = 10
SEARCH_LIMIT = 15

st.set_page_config(page_title="Music Wrapped", page_icon="🎵", layout="wide")


@st.cache_resource(show_spinner="Loading catalog and personality model…")
def load_app_data() -> tuple[pd.DataFrame, pd.DataFrame, dict | None]:
    raw = load_dataset()
    scaled, _ = scale_features(raw)
    artifacts = load_artifacts(ARTIFACT_PATH) if ARTIFACT_PATH.exists() else None
    return raw, scaled, artifacts


df_raw, df_scaled, artifacts = load_app_data()

if artifacts is None:
    st.error(
        f"Personality artifact not found at `{ARTIFACT_PATH.relative_to(ROOT)}`. "
        "Run `notebooks/02_clustering.ipynb` end-to-end to generate it, then refresh."
    )
    st.stop()

st.session_state.setdefault("selected", [])
st.session_state.setdefault("show_wrapped", False)


def add_song(track_id: str) -> None:
    sel = st.session_state.selected
    if track_id not in sel and len(sel) < MAX_SEEDS:
        sel.append(track_id)


def remove_song(track_id: str) -> None:
    if track_id in st.session_state.selected:
        st.session_state.selected.remove(track_id)


def clear_selection() -> None:
    st.session_state.selected = []
    st.session_state.show_wrapped = False


# ──────────────────────────── Header ────────────────────────────
st.title("🎵 Music Wrapped")
st.caption(
    f"Pick {MIN_SEEDS}–{MAX_SEEDS} songs you've been listening to and we'll tell you "
    "who you are as a listener — mood, music personality, your audio DNA, and what to play next."
)

# ──────────────────────────── Selection ────────────────────────────
left, right = st.columns([2, 1])

with left:
    st.subheader("Pick your songs")
    query = st.text_input(
        "Search by track or artist",
        placeholder="e.g., billie eilish, fortunate son, daft punk",
        label_visibility="collapsed",
    )
    if query:
        ql = query.lower()
        mask = (
            df_raw["track_name"].str.lower().str.contains(ql, na=False)
            | df_raw["track_artist"].str.lower().str.contains(ql, na=False)
        )
        matches = df_raw.loc[mask].head(SEARCH_LIMIT)
        if matches.empty:
            st.caption("No matches. Try a different query.")
        else:
            for _, row in matches.iterrows():
                tid = row["track_id"]
                already = tid in st.session_state.selected
                full = len(st.session_state.selected) >= MAX_SEEDS
                label = f"{row['track_name']} — {row['track_artist']}"
                st.button(
                    f"{'✓' if already else '+'} {label}",
                    key=f"add_{tid}",
                    on_click=add_song,
                    args=(tid,),
                    disabled=already or full,
                    use_container_width=True,
                )

with right:
    n_sel = len(st.session_state.selected)
    st.subheader(f"Selected {n_sel}/{MAX_SEEDS}")
    if n_sel == 0:
        st.caption(f"Empty — search and add at least {MIN_SEEDS} songs.")
    for tid in list(st.session_state.selected):
        rows = df_raw.loc[df_raw["track_id"] == tid]
        if rows.empty:
            continue
        row = rows.iloc[0]
        c1, c2 = st.columns([5, 1])
        c1.write(f"**{row['track_name']}** — {row['track_artist']}")
        c2.button("✕", key=f"rm_{tid}", on_click=remove_song, args=(tid,))
    if n_sel:
        st.button("Clear all", on_click=clear_selection, type="secondary")

ready = MIN_SEEDS <= n_sel <= MAX_SEEDS
generate = st.button(
    "✨ Generate My Wrapped",
    type="primary",
    disabled=not ready,
    use_container_width=True,
)
if generate:
    st.session_state.show_wrapped = True

if not st.session_state.show_wrapped:
    st.stop()

# ──────────────────────────── Wrapped sections ────────────────────────────
seed_raw = df_raw.loc[df_raw["track_id"].isin(st.session_state.selected)]
seed_scaled = df_scaled.loc[df_scaled["track_id"].isin(st.session_state.selected)]

st.divider()


def section_numbers() -> None:
    st.header("🎶 Your Music in Numbers")
    c1, c2, c3 = st.columns(3)
    c1.metric("Songs", len(seed_raw))
    c2.metric("Unique artists", seed_raw["track_artist"].nunique())
    top_genre = seed_raw["playlist_genre"].mode().iloc[0]
    c3.metric("Top genre", top_genre)

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Genres in your selection**")
        gc = seed_raw["playlist_genre"].value_counts()
        fig = px.bar(gc[::-1], orientation="h", labels={"value": "tracks", "index": ""})
        fig.update_layout(showlegend=False, height=max(180, 32 * len(gc)), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
    with g2:
        st.markdown("**Top artists**")
        artists = seed_raw["track_artist"].value_counts().head(5)
        for name, count in artists.items():
            st.write(f"• **{name}** — {count} track{'s' if count != 1 else ''}")


def section_mood() -> None:
    st.header("🎭 Your Mood")
    mean_v = float(seed_raw["valence"].mean())
    mean_e = float(seed_raw["energy"].mean())
    mood = classify_mood(mean_v, mean_e)
    st.markdown(f"# You are **{mood}**.")
    st.write(MOOD_DESCRIPTIONS.get(mood, MOOD_FALLBACK))

    bg = df_raw.sample(min(800, len(df_raw)), random_state=42)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=bg["valence"], y=bg["energy"], mode="markers",
        marker=dict(size=4, color="lightgray", opacity=0.5),
        name="Catalog (sample)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=seed_raw["valence"], y=seed_raw["energy"], mode="markers",
        marker=dict(size=14, color="#1DB954", line=dict(color="white", width=1.5)),
        name="Your songs",
        text=seed_raw["track_name"] + " — " + seed_raw["track_artist"],
        hovertemplate="%{text}<br>valence=%{x:.2f}<br>energy=%{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[mean_v], y=[mean_e], mode="markers+text",
        marker=dict(size=22, color="#FF7A1A", symbol="star", line=dict(color="white", width=1.5)),
        name="Your average", text=["★"], textposition="middle center",
        hovertemplate=f"Your avg<br>valence={mean_v:.2f}<br>energy={mean_e:.2f}<extra></extra>",
    ))
    fig.add_vline(x=0.6, line_dash="dot", line_color="gray")
    fig.add_vline(x=0.35, line_dash="dot", line_color="gray")
    fig.add_hline(y=0.6, line_dash="dot", line_color="gray")
    fig.update_layout(
        xaxis_title="valence (low → high)", yaxis_title="energy (low → high)",
        xaxis=dict(range=[0, 1]), yaxis=dict(range=[0, 1]),
        height=480, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)


def section_personality() -> None:
    st.header("🧬 Your Music Personality")
    archetype = predict_personality(seed_raw, artifacts)
    st.markdown(f"# You're a **{archetype}**.")
    st.write(ARCHETYPE_DESCRIPTIONS.get(archetype, ARCHETYPE_FALLBACK))

    centroid_idx = list(artifacts["label_map"].values()).index(archetype)
    centroid = artifacts["kmeans"].cluster_centers_[centroid_idx]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(centroid) + [centroid[0]],
        theta=AUDIO_FEATURES + [AUDIO_FEATURES[0]],
        fill="toself", name=archetype, line=dict(color="#1DB954"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=420, margin=dict(l=40, r=40, t=20, b=20), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def section_audio_dna() -> None:
    st.header("🧪 Your Audio DNA")
    user_profile = seed_scaled[AUDIO_FEATURES].mean()
    catalog_mean = df_scaled[AUDIO_FEATURES].mean()
    delta = (user_profile - catalog_mean).sort_values()
    above = delta.tail(2).index.tolist()[::-1]
    below = delta.head(2).index.tolist()

    st.write(
        f"Above average for **{above[0]}** and **{above[1]}** · "
        f"below average for **{below[0]}** and **{below[1]}**."
    )

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(catalog_mean) + [catalog_mean.iloc[0]],
        theta=AUDIO_FEATURES + [AUDIO_FEATURES[0]],
        name="Average listener", line=dict(color="lightgray"),
    ))
    fig.add_trace(go.Scatterpolar(
        r=list(user_profile) + [user_profile.iloc[0]],
        theta=AUDIO_FEATURES + [AUDIO_FEATURES[0]],
        fill="toself", name="You", line=dict(color="#1DB954"),
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=420, margin=dict(l=40, r=40, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)


def _format_recs(recs: pd.DataFrame, include_pop: bool = False) -> pd.DataFrame:
    cols = {
        "track_name": "Track",
        "track_artist": "Artist",
        "similarity": "Similarity",
    }
    if include_pop:
        cols["track_popularity"] = "Popularity"
    out = recs.reset_index(drop=True)[list(cols)].rename(columns=cols)
    out.index = np.arange(1, len(out) + 1)
    out.index.name = "#"
    return out


_RECS_CACHE: dict = {}


def _compute_recs() -> pd.DataFrame:
    if "df" not in _RECS_CACHE:
        recs = recommend(df_scaled, seed_scaled, n=10).join(
            df_raw[["track_name", "track_artist", "track_popularity"]],
            rsuffix="_raw",
        )
        _RECS_CACHE["df"] = recs
    return _RECS_CACHE["df"]


def section_recommendations() -> None:
    st.header("🎯 Top Recommendations")
    st.caption(
        "Cosine similarity to your average audio profile, with a small popularity nudge (α = 0.95)."
    )
    recs = _compute_recs()
    table = _format_recs(recs)
    st.dataframe(
        table,
        use_container_width=True,
        column_config={
            "Similarity": st.column_config.ProgressColumn(
                "Similarity", format="%.3f", min_value=0.0, max_value=1.0
            ),
        },
    )


def section_hidden_gems() -> None:
    st.header("💎 Hidden Gems")
    st.caption(
        "High audio similarity, but below the lower of the catalog median or your average seed popularity. "
        "Disjoint from the main recommendations above."
    )
    rec_idx = list(_compute_recs().index)
    gems = hidden_gems(df_scaled, seed_scaled, top_pct=0.10, n=8, exclude=rec_idx).join(
        df_raw[["track_name", "track_artist", "track_popularity"]],
        rsuffix="_raw",
    )
    if gems.empty:
        st.info("No gems passed the popularity ceiling for this selection.")
        return
    table = _format_recs(gems, include_pop=True)
    st.dataframe(
        table,
        use_container_width=True,
        column_config={
            "Similarity": st.column_config.ProgressColumn(
                "Similarity", format="%.3f", min_value=0.0, max_value=1.0
            ),
            "Popularity": st.column_config.ProgressColumn(
                "Popularity", format="%d", min_value=0, max_value=100
            ),
        },
    )


for section in (
    section_numbers,
    section_mood,
    section_personality,
    section_audio_dna,
    section_recommendations,
    section_hidden_gems,
):
    section()
    st.divider()

st.caption("CPTS 315 final project — Boakye, Son, Zarate, Lewis · 2026")
