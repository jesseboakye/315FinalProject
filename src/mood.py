"""Rule-based mood classification from valence and energy.

Thresholds tuned from EDA: high at 0.6, low-valence at 0.35.
"""

import pandas as pd

HIGH = 0.6
LOW_VALENCE = 0.35
LOW_ENERGY = 0.4


def classify_mood(valence: float, energy: float) -> str:
    if valence >= HIGH and energy >= HIGH:
        return "Euphoric"
    if valence >= HIGH and energy < HIGH:
        return "Chill & Happy"
    if valence < LOW_VALENCE and energy >= HIGH:
        return "Dark & Intense"
    if valence < LOW_VALENCE and energy < LOW_ENERGY:
        return "Melancholic"
    if energy >= HIGH:
        return "Driven"
    return "Balanced"


def profile_mood(seed_df: pd.DataFrame) -> str:
    return classify_mood(seed_df["valence"].mean(), seed_df["energy"].mean())
