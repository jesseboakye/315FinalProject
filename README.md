# 315FinalProject — Music Recommendation System

CPTS 315 final project: an interactive Spotify Wrapped-style music discovery system. Users select 3–10 seed songs and receive a personalized breakdown — top genres/artists, mood, music personality archetype, audio profile, recommendations, and hidden gems.

## Team
Jesse Boakye, Kenneth Son, Luis Zarate, Ralph Lewis

## Pipeline
1. Preprocessing — load Kaggle Spotify dataset, clean, dedupe, MinMax-scale audio features
2. EDA — distributions, correlations, genre balance
3. Clustering — K-means on normalized audio features for music personality archetypes
4. Recommendation — cosine similarity vs. user's average feature vector
5. Mood — rule-based valence/energy classifier
6. Hidden gems — top 10–15% most similar tracks below the user's average popularity
7. Wrapped report — Streamlit UI
8. Evaluation — silhouette, elbow, genre consistency, intra-list diversity, leave-one-out seed recovery

## Tech Stack
Python · pandas · numpy · scikit-learn · matplotlib · seaborn · Streamlit · plotly

## Plan
Baseline: implementation plan PDF. Active deltas (feedback + EDA-driven): [docs/plan-adjustments.md](docs/plan-adjustments.md).

## Dataset
[Spotify Music Dataset (Kaggle)](https://www.kaggle.com/datasets/solomonameh/spotify-music-dataset) — place CSV(s) under `data/` (gitignored).

## Project Layout
```
src/
  preprocessing.py
  eda.py
  clustering.py
  recommend.py
  mood.py
  hidden_gems.py
  evaluation.py
  features.py
app/
  streamlit_app.py
notebooks/
data/                # gitignored
artifacts/           # gitignored
```

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

## Run the demo
```bash
streamlit run app/streamlit_app.py
```
