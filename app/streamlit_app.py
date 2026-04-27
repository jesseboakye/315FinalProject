"""Streamlit Wrapped-style demo. Run: streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(page_title="Music Wrapped", layout="wide")
st.title("Music Wrapped")
st.caption("CPTS 315 final project — interactive music discovery")

st.info("Skeleton app. Wire up data loading, song selection, mood, personality, recs, and hidden gems.")
