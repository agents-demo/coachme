"""Streamlit UI for CoachMe — a video-first coaching journey.

Pages: Sessions (history) -> Analyze -> Result -> Practice -> Progress -> You.

Run:
    streamlit run coachme/surfaces/gui/ui.py
"""

from __future__ import annotations

import streamlit as st

from coachme.surfaces.gui import nav
from coachme.surfaces.gui.app_pages import analyze, practice, profile, progress, result, sessions

st.set_page_config(page_title="CoachMe", page_icon="🏓", layout="centered")

nav.PAGE_OBJS.update(
    {
        "Sessions": st.Page(sessions.page, title="Sessions", icon="📋", url_path="sessions", default=True),
        "Analyze": st.Page(analyze.page, title="Analyze", icon="🎬", url_path="analyze"),
        "Practice": st.Page(practice.page, title="Practice", icon="🏋️", url_path="practice"),
        "Progress": st.Page(progress.page, title="Progress", icon="📈", url_path="progress"),
        "You": st.Page(profile.page, title="You", icon="👤", url_path="you"),
        "Result": st.Page(result.page, title="Result", icon="🏓", url_path="result"),
    }
)

_nav = st.navigation([nav.PAGE_OBJS[k] for k in ("Sessions", "Analyze", "Practice", "Progress", "You", "Result")])
_nav.run()
