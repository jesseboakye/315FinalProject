"""EDA helpers: distributions, correlations, genre balance."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .features import AUDIO_FEATURES


def feature_distributions(df: pd.DataFrame):
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    for ax, feat in zip(axes.flat, AUDIO_FEATURES):
        sns.histplot(df[feat], ax=ax, bins=40, kde=True)
        ax.set_title(feat)
    fig.tight_layout()
    return fig


def correlation_heatmap(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(df[AUDIO_FEATURES].corr(), annot=True, cmap="coolwarm", ax=ax)
    return fig
