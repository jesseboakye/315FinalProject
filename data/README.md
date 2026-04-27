# Data

Place the raw Kaggle Spotify Music Dataset CSV(s) here. Files in this directory are gitignored.

Source: https://www.kaggle.com/datasets/solomonameh/spotify-music-dataset

Expected files:
- `high_popularity_spotify_data.csv`
- `low_popularity_spotify_data.csv`

`src/preprocessing.load_dataset()` concatenates both, dedupes by `track_id`, and drops rows missing any of the modeling audio features.
