"""Rule-based mood classification from valence and energy."""

import pandas as pd


def classify_mood(valence: float, energy: float) -> str:
    if valence >= 0.6 and energy >= 0.6:
        return "Euphoric"
    if valence >= 0.6 and energy < 0.6:
        return "Chill & Happy"
    if valence < 0.4 and energy >= 0.6:
        return "Dark & Intense"
    if valence < 0.4 and energy < 0.4:
        return "Melancholic"
    if energy >= 0.6:
        return "Driven"
    return "Balanced"


def profile_mood(seed_df: pd.DataFrame) -> str:
    return classify_mood(seed_df["valence"].mean(), seed_df["energy"].mean())
