"""Load and clean the Spotify dataset; MinMax-scale audio features."""

from pathlib import Path

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from .features import AUDIO_FEATURES

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
HIGH_POP = DATA_DIR / "high_popularity_spotify_data.csv"
LOW_POP = DATA_DIR / "low_popularity_spotify_data.csv"


def load_dataset(high_path: Path = HIGH_POP, low_path: Path = LOW_POP) -> pd.DataFrame:
    high = pd.read_csv(high_path)
    low = pd.read_csv(low_path)
    df = pd.concat([high, low], ignore_index=True)
    df = df.drop_duplicates(subset=["track_id"], keep="first")
    df = df.dropna(subset=AUDIO_FEATURES + ["track_name", "track_artist"])
    return df.reset_index(drop=True)


def scale_features(df: pd.DataFrame) -> tuple[pd.DataFrame, MinMaxScaler]:
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[AUDIO_FEATURES])
    out = df.copy()
    out[AUDIO_FEATURES] = scaled
    return out, scaler
