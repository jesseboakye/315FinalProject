# Phase 7 Plan — Streamlit Wrapped Demo

## Goal

Ship a single-file Streamlit app that takes 3–10 user-picked songs and produces a Spotify-Wrapped-style report covering mood, personality archetype, audio DNA, recommendations, and hidden gems. The app is the demo deliverable for the project; everything else feeds into it.

## UX flow

Single scrollable page (no multi-page nav — judges shouldn't have to click "next" five times during a demo).

```
┌─────────────────────────────────────────┐
│   🎵 Music Wrapped         (header)     │
│   Pick 3–10 songs to get your report.   │
├─────────────────────────────────────────┤
│   [search box]    │ Selected (5/10)     │
│   ── matches ──   │ • Song A   ✕        │
│   + Song X        │ • Song B   ✕        │
│   + Song Y        │ • Song C   ✕        │
│   + Song Z        │ • Song D   ✕        │
│                   │ • Song E   ✕        │
├─────────────────────────────────────────┤
│   [   ✨ Generate My Wrapped   ]        │
├─────────────────────────────────────────┤
│   Slide 1 — Your Music in Numbers       │
│   Slide 2 — Your Mood                   │
│   Slide 3 — Your Music Personality      │
│   Slide 4 — Your Audio DNA              │
│   Slide 5 — Top Recommendations         │
│   Slide 6 — Hidden Gems                 │
└─────────────────────────────────────────┘
```

**Empty state**: only the picker is visible. The Generate button is disabled until ≥ 3 songs are selected. Adding past 10 is blocked.

**After Generate**: slides expand below the picker, each with a clear `st.divider()` between them. The picker stays in place at the top so the user can swap songs and re-generate.

## Slide-by-slide design

### 1. Your Music in Numbers
- Three big metrics row: # songs, # unique artists, top genre.
- Horizontal bar chart of genre counts in the selection.
- Top 5 artists list (count of tracks, ties broken alphabetically).

### 2. Your Mood
- Hero text: "You are **{mood}**." (from `mood.profile_mood`)
- One-sentence description per mood label.
- 2D scatter of the user's selected songs in valence × energy space, with quadrant lines at 0.6 (high) and 0.35 (low valence) per the EDA-tuned thresholds. Background lightly seeded with a sample of the catalog for context.

### 3. Your Music Personality
- Hero text: archetype name (e.g., "You're a **Lofi Wanderer**.")
- One-sentence flavor text per archetype.
- Radar chart of the cluster centroid's 8-feature profile (the personality's signature).
- Note: works without back-projection because Track A won — centroids live in the original feature space.

### 4. Your Audio DNA
- Radar of the user's average MinMax-scaled profile vs the catalog mean. Shows what makes the user's taste distinctive.
- Quick callout: top 2 features above average, top 2 below.

### 5. Top Recommendations
- Top 10 from `recommend(catalog, seed)` (default α = 0.95).
- Table: rank, track, artist, similarity bar (visual % via column config).
- **No genre column** — the dataset's `playlist_genre` tags songs with the genre of the playlist they were scraped from, not the song's own genre, which produces visibly wrong per-track labels. See [plan-adjustments.md → Phase 7](plan-adjustments.md). Captions explain the ranking is based on cosine similarity to the user's average audio profile.

### 6. Hidden Gems
- Top 5 from `hidden_gems(catalog, seed)`.
- Same table format as recommendations + popularity column to show these are genuinely lower-popularity.
- Callout text explaining the adaptive popularity ceiling.

## Tech approach

- **Data + artifact loading** under `@st.cache_resource` — runs once per session, not per interaction.
- **Selection state** in `st.session_state["selected"]` — list of `track_id` strings.
- **Search** is a case-insensitive substring match on `track_name | track_artist`, capped at 15 results to keep the UI lean.
- **Charts**: Plotly for the radars and the mood scatter (interactive, easy hover info). Streamlit native for tables and metrics.
- **No DB, no API calls** — entirely offline, runs against the local CSVs and the joblib artifact.
- **Defensive load**: if `artifacts/personality_v1.joblib` is missing, the app shows a friendly message pointing the user at `notebooks/02_clustering.ipynb`.

## File structure

```
app/
  streamlit_app.py     # main entry — UI + cache + state
  copy.py              # mood + archetype flavor text (lookup dicts)
```

Keep it to two files. `copy.py` exists only so the long descriptive strings don't clutter the layout code; everything else stays in the main app.

## Acceptance criteria

- [ ] App launches with `streamlit run app/streamlit_app.py` in under 3 seconds (after the first cache build).
- [ ] Picker accepts 3–10 songs; Generate disabled outside that range.
- [ ] All six slides render without errors on a representative seed (e.g., 5 latin tracks, 5 classical tracks, 5 mixed).
- [ ] Mood and personality match the standalone module outputs (no UI-side recomputation drift).
- [ ] Recommendations and hidden gems are non-overlapping in 5/5 spot-checks.
- [ ] Re-generating after swapping a song updates all slides.
- [ ] No tracebacks in the terminal during a 5-minute demo session.

## Risks

- **Search latency** — substring on 4,494 rows is fine; if we ever expand the catalog, swap in a prefix index or fuzzy matcher.
- **Streamlit reruns** — every widget interaction reruns the script. Cache the data + artifact load aggressively; keep all per-interaction work in O(catalog) or smaller.
- **Plotly font sizes** — the radar legend labels can clip on narrow viewports. Set explicit margins.
- **Cold-start aesthetics** — the empty page should still feel alive: include a one-line tip and maybe a "Try a sample seed" button (stretch).

## Out of scope (this phase)

- Spotify API integration / live track previews.
- Login or per-user persistence.
- Mood trajectory playlists, GMM soft labels, or weighted cosine — all stretch goals tracked in `plan-adjustments.md`.
- Multi-page navigation.

## Definition of done

`app/streamlit_app.py` runs end-to-end, all six slides render correctly for at least three distinct seed sets, and the app is screen-shot-able for the final report.
