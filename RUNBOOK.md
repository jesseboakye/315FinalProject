# Runbook — running the project end to end

For the four of us. Get from a fresh clone to a running demo, regenerated report figures, and a built deck without guessing.

If anything below fails, the **Troubleshooting** section at the bottom covers the cases we've actually hit.

---

## 0. One-time setup

You only need to do this once per machine.

### 0.1 Clone the repo

```bash
git clone https://github.com/jesseboakye/315FinalProject.git
cd 315FinalProject
```

### 0.2 Pick the right branch

If you're picking up the worktree branch:
```bash
git fetch
git checkout claude/busy-blackwell-279713    # or whatever branch is current
```

If main has the merged work, just stay on main.

### 0.3 Create a virtual environment + install deps

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (cmd):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` covers pandas, numpy, scikit-learn, joblib, matplotlib, seaborn, streamlit, plotly, and jupyter.

If you also want to build slides or the report yourself:
```bash
pip install python-pptx "markitdown[pptx]"
```

### 0.4 Drop the dataset into `data/`

The dataset is **gitignored** — it's not in the repo. Download both CSVs from the Kaggle Spotify Music Dataset:
<https://www.kaggle.com/datasets/solomonameh/spotify-music-dataset>

Place them at:
```
data/high_popularity_spotify_data.csv
data/low_popularity_spotify_data.csv
```

`src/preprocessing.load_dataset()` automatically concatenates both, dedupes by `track_id`, and drops rows with missing modeling features.

### 0.5 Sanity-check the install

```bash
python -c "from src.preprocessing import load_dataset; df = load_dataset(); print(df.shape)"
```

Expected: `(4494, 29)`. If you see this, you're good.

---

## 1. Reproduce the modeling pipeline (notebooks)

Run these **in order**. Notebook 02 produces the artifact that the Streamlit app loads, so don't skip it.

### 1.1 Launch Jupyter

```bash
jupyter notebook
```

(Or use VS Code / JupyterLab — whatever opens `.ipynb`.)

### 1.2 Run notebook 01 — EDA

`notebooks/01_eda.ipynb`

What it does:
- Loads + cleans the catalog
- Audio-feature distributions, correlation heatmap
- Genre balance, popularity distributions
- Per-genre audio profile (used to label clusters)
- Mood quadrants (valence × energy)
- PCA 2D + cumulative variance

**Run all cells.** Output is purely informational — nothing is persisted to disk.

Expected runtime: ~30 seconds.

### 1.3 Run notebook 02 — clustering

`notebooks/02_clustering.ipynb`

What it does:
- Two-track K-means experiment (8 features vs 6-component PCA)
- Elbow + silhouette across K = 2..10, restricted to K ∈ [5, 8]
- Picks K=6 on Track A (silhouette 0.252)
- Labels six archetypes (Lofi Wanderer, Night Driver, Life of the Party, The Old Soul, The Sonic Architect, Acoustic Storyteller)
- **Persists `artifacts/personality_v1.joblib`** — this is what Streamlit consumes

**Run all cells.** When it completes, you should have:
```
artifacts/personality_v1.joblib   (~20 KB)
```

Expected runtime: ~1 minute.

### 1.4 Run notebook 03 — evaluation

`notebooks/03_evaluation.ipynb`

What it does:
- Leave-one-out seed recovery (200 simulated users × 5 seeds × 2 strategies)
- Hit Rate @ K, MRR, mean/median rank
- Genre consistency, intra-list diversity, hidden-gem overlap
- Alpha sweep (popularity-blend trade-off)
- Cosine vs Euclidean comparison

**Run all cells.** Output is informational; no artifacts persisted.

Expected runtime: ~3 minutes (LOO across 1,000 trials per strategy is the slow part).

---

## 2. Run the Streamlit demo

The demo is the project deliverable.

```bash
streamlit run app/streamlit_app.py
```

If `streamlit` isn't on PATH (common on Windows with `--user` installs):
```bash
python -m streamlit run app/streamlit_app.py
```

The app opens at <http://localhost:8501>. First-time load takes ~5 seconds (catalog + artifact cache); subsequent reruns are instant.

### Smoke test

1. Type a search like `billie eilish` in the search box.
2. Click `+` next to **3–10** matching tracks.
3. Click **✨ Generate My Wrapped**.
4. Six slides should render below the picker, in order: Music in Numbers → Mood → Music Personality → Audio DNA → Top Recommendations → Hidden Gems.

### What the slides should show

| Slide | What you should see |
|---|---|
| Music in Numbers | Three metric cards (songs, artists, top genre) + horizontal genre bar chart + top-5 artists list |
| Your Mood | A mood label (e.g., "Euphoric") in big text + descriptive sentence + valence/energy scatter with your songs in green and your average as an orange star |
| Music Personality | An archetype label (e.g., "You're a Life of the Party") + descriptive sentence + radar chart of the cluster centroid |
| Audio DNA | A two-trace radar (your profile vs catalog mean) + a sentence highlighting your top above/below features |
| Top Recommendations | Numbered table with Track, Artist, and a similarity progress bar |
| Hidden Gems | Same as recommendations + a popularity progress bar; **disjoint** from the recs |

If the personality artifact is missing, the app shows a friendly error pointing you back at notebook 02.

### Stopping the server

`Ctrl+C` in the terminal running Streamlit.

---

## 3. Regenerate report figures (optional)

If you change the catalog, the clustering, or the evaluation, regenerate all 14 figures:

```bash
python docs/report/generate_figures.py
```

Output goes to `docs/report/figures/*.png`. The script:
- loads the dataset
- re-runs everything needed for each figure (no cache)
- writes 14 PNGs at high resolution

Expected runtime: ~2 minutes.

---

## 4. Build the IEEE report (optional, for re-compilation)

The LaTeX source is at `docs/report/main.tex` with the IEEE class files alongside.

### Easiest: Overleaf
1. Upload everything in `docs/report/` (including `figures/`) to a new Overleaf project.
2. Set main document = `main.tex`.
3. Compile.

### Local LaTeX install (if you have one)
```bash
cd docs/report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

`main.pdf` ends up in the same folder.

---

## 5. Rebuild the presentation deck (optional)

The deck is `docs/report/presentation.pptx` (12 slides, 16:9). To rebuild:

```bash
python docs/report/build_pptx.py
```

Pre-req:
```bash
pip install python-pptx
```

The script reads from `docs/report/figures/`, so make sure those exist (Section 3).

---

## 6. Project layout cheat sheet

```
src/                 — modeling code (preprocessing, clustering, recommend, ...)
app/                 — Streamlit demo
notebooks/           — 01_eda · 02_clustering · 03_evaluation
artifacts/           — gitignored; personality_v1.joblib lands here after notebook 02
data/                — gitignored; you place the Kaggle CSVs here
docs/
  plan-adjustments.md         — running deltas vs. the implementation plan PDF
  phase3-clustering-plan.md   — clustering phase plan
  phase7-streamlit-plan.md    — Streamlit phase plan
  report/                     — IEEE LaTeX paper + figures + presentation deck
  template/                   — original IEEE template (reference only)
RUNBOOK.md           — this file
README.md            — short intro + links
requirements.txt     — Python deps
```

---

## 7. Troubleshooting

### `streamlit: command not found`
Use `python -m streamlit run app/streamlit_app.py`. The PowerShell scripts that ship with `pip install --user streamlit` aren't always on PATH on Windows.

### `Personality artifact not found`
You haven't run `notebooks/02_clustering.ipynb` yet. The Streamlit app needs `artifacts/personality_v1.joblib`. Run all cells of notebook 02 to generate it.

### `data/...csv: No such file or directory`
You haven't put the Kaggle CSVs in `data/`. See step 0.4. Both files (`high_popularity_spotify_data.csv` and `low_popularity_spotify_data.csv`) are required.

### Streamlit shows the *old* "Skeleton app" page
You're running an outdated branch. Pull the latest, or check out `claude/busy-blackwell-279713` (or whichever branch holds the current work). Streamlit auto-reloads when you save the file, but won't pull new code on its own.

### `recommend()` and `hidden_gems()` return overlapping tracks
Make sure you're calling the version that takes `exclude=`. The Streamlit app passes the rec indices into `hidden_gems(..., exclude=rec_idx)` to keep the surfaces disjoint at α=0.95. If you're scripting outside the app, do the same.

### Notebook 02 picks K=2 instead of K=6
You're running an old version of the decision-rule cell. The current rule restricts to K ∈ [5, 8] before picking by silhouette. Pull the latest and rerun.

### Notebook execution complains about missing kernel
```bash
python -m ipykernel install --user --name=315FinalProject
```
Then pick the `315FinalProject` kernel in Jupyter.

### `pip install` hangs or is glacial
Use the cached wheel index:
```bash
pip install --upgrade pip
pip install --prefer-binary -r requirements.txt
```

### `python-pptx` save fails with a Unicode error
That's a Windows console-printing issue, not a PPTX bug. The file saves fine; the error is on the trailing `print` line. The `build_pptx.py` script uses ASCII output already.

### Figures look clipped in the LaTeX PDF
Check the `\includegraphics[width=0.48\textwidth]` line — the figures are sized for the IEEE two-column layout. If you compile single-column, bump to `0.95\textwidth`.

---

## 8. Who owns what

| Area | Default owner |
|---|---|
| `src/preprocessing.py`, EDA notebook | Anyone — small surface |
| `src/clustering.py`, notebook 02, archetype labels | Whoever runs the K-means experiment next |
| `src/recommend.py`, `src/hidden_gems.py`, evaluation notebook | Whoever owns recommender tuning |
| `app/streamlit_app.py`, `app/copy.py` | Demo lead |
| `docs/report/main.tex` | Report lead |
| `docs/report/build_pptx.py`, `presentation.pptx` | Slides lead |

When in doubt, the answer is in `docs/plan-adjustments.md` — that file is the running record of every decision we changed from the original plan PDF and why.

---

## 9. Quick smoke-test for "is everything still working?"

After a fresh clone + setup, this five-step check confirms the entire stack:

```bash
# 1. data loads
python -c "from src.preprocessing import load_dataset; print(load_dataset().shape)"
# expect: (4494, 29)

# 2. clustering artifact exists (run notebook 02 if not)
python -c "from pathlib import Path; print(Path('artifacts/personality_v1.joblib').exists())"
# expect: True

# 3. the personality predict round-trip works
python -c "
from src.preprocessing import load_dataset
from src.artifacts import load_artifacts, predict_personality, ARTIFACTS_DIR
df = load_dataset()
a = load_artifacts(ARTIFACTS_DIR / 'personality_v1.joblib')
seed = df[df['playlist_genre']=='lofi'].head(5)
print('5 lofi tracks ->', predict_personality(seed, a))
"
# expect: a sensible archetype name (often 'The Old Soul' for lofi)

# 4. streamlit boots
python -m streamlit run app/streamlit_app.py --server.headless true --server.port 8765 &
sleep 5
curl -sf http://localhost:8765/_stcore/health
# expect: ok
kill %1

# 5. figures regenerate
python docs/report/generate_figures.py
# expect: "Done. 14 figures written to ..."
```

If all five pass, you're set up correctly.
