"""Page: Practice."""

from __future__ import annotations

import streamlit as st

from topspin_review.surfaces.gui import data, nav, style
from topspin_review.surfaces.gui.job import prelude


def page() -> None:
    prelude()
    style.hero("Practice", "Turn the report's drills into this week's plan.")
    latest = data.latest_report()
    if not latest:
        st.info("Analyze a video or photo first, then your drills will show up here.")
        if st.button("Analyze a video or photo", type="primary"):
            nav.go("Analyze")
        return

    if latest.get("focus"):
        st.success(f"**Focus:** {latest['focus']}")
    drills = latest.get("drills") or []
    if not drills:
        st.info("No drills in the latest report.")
        return

    st.markdown("### This week's drills")
    done = 0
    for i, drill in enumerate(drills):
        if st.checkbox(drill, key=f"drill_{i}"):
            done += 1
    st.progress(done / len(drills) if drills else 0.0, text=f"{done}/{len(drills)} drills checked off")
