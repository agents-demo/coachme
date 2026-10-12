"""Page: Progress."""

from __future__ import annotations

import streamlit as st

from topspin_review.domain import compare as compare_mod
from topspin_review.domain import render
from topspin_review.integrations.storage import store
from topspin_review.surfaces.gui import style
from topspin_review.surfaces.gui.job import prelude


def page() -> None:
    prelude()
    style.hero("Progress", "How your game is trending across sessions.")
    reports = store.get_reports()
    if not reports:
        st.info("Analyze a few sessions to see your progress.")
        return
    latest = reports[-1]
    trend = latest.get("progress_trend") or {}
    st.write(trend.get("text", "Not enough history yet."))

    counts = trend.get("issue_counts") or []
    if counts:
        st.markdown("### Issues per session (lower is better)")
        st.line_chart({"issues": counts})

    if len(reports) >= 2:
        with st.expander("Compare two sessions"):
            names = [render.video_name(r) for r in reports]
            left, right = st.columns(2)
            older = left.selectbox("Earlier", names, index=0)
            newer = right.selectbox("Later", names, index=len(names) - 1)
            if st.button("Compare") and older != newer:
                result = compare_mod.compare(reports[names.index(older)], reports[names.index(newer)])
                st.markdown(f"**What changed:** {result['text']}")
                for label, key in (("Improved", "improved"), ("Still an issue", "unchanged"), ("New/regressed", "regressed")):
                    items = result.get(key) or []
                    if items:
                        st.markdown(f"**{label}:** " + ", ".join(items))
