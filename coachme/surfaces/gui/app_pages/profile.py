"""Page: You (profile)."""

from __future__ import annotations

import streamlit as st

from coachme.integrations.storage import store
from coachme.surfaces.gui import config, style
from coachme.surfaces.gui.job import prelude


def page() -> None:
    prelude()
    style.hero("You", "Your sport, level, and what you're working on.")
    profile = store.get_profile()
    st.markdown("### Your profile")
    sport = st.radio(
        "Sport",
        config.SPORTS,
        index=config.SPORTS.index(profile["sport"]) if profile.get("sport") in config.SPORTS else 0,
        horizontal=True,
    )
    level = st.radio(
        "Level",
        config.LEVELS,
        index=config.LEVELS.index(profile["level"]) if profile.get("level") in config.LEVELS else 1,
        horizontal=True,
    )
    hand = st.radio(
        "Dominant hand",
        config.HANDS,
        index=config.HANDS.index(profile["dominant_hand"]) if profile.get("dominant_hand") in config.HANDS else 0,
        horizontal=True,
    )
    goal = st.text_input("What you want to improve", value=profile.get("goal", "improve"))
    if st.button("Save profile", type="primary"):
        store.set_profile({"sport": sport, "level": level, "dominant_hand": hand, "goal": goal})
        st.success("Saved.")

    st.divider()
    if store.get_reports():
        if st.button("Clear all reports"):
            store.reset()
            st.session_state["latest_stem"] = None
            st.rerun()
