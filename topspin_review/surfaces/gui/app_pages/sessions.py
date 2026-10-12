"""Page: Sessions (history)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from topspin_review.domain import render
from topspin_review.integrations.storage import store
from topspin_review.surfaces.gui import nav, style
from topspin_review.surfaces.gui.job import prelude


def page() -> None:
    prelude()
    style.hero("Sessions", "Every video or photo you've analyzed — open one or analyze a new clip.")

    reports = store.get_reports()
    if st.button("Analyze a new video or photo", type="primary"):
        nav.go("Analyze")
    if not reports:
        st.info("No sessions yet. Click **Analyze a new video or photo** to get started.")
        return

    latest = reports[-1]
    st.markdown("### Current focus")
    st.success(latest.get("focus") or "Keep up the consistency work.")

    st.markdown("### History")
    for report in reversed(reports):
        stem = Path(report.get("source", "")).stem
        if st.session_state.get("confirm_delete") == stem:
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.warning(f"Delete **{render.video_name(report)}**?")
            if c2.button("Delete", key=f"confirm_{stem}", type="primary"):
                store.delete_report(stem)
                if st.session_state.get("latest_stem") == stem:
                    st.session_state["latest_stem"] = None
                st.session_state.pop(f"qa_{stem}", None)
                st.session_state["confirm_delete"] = None
                st.rerun()
            if c3.button("Cancel", key=f"cancel_{stem}"):
                st.session_state["confirm_delete"] = None
                st.rerun()
            continue
        c1, c2, c3 = st.columns([8, 1, 1])
        c1.markdown(f"**{render.video_name(report)}**  \n{report.get('date', '')} — {report.get('focus', '')}")
        if c2.button("Open", key=f"open_{stem}"):
            nav.open_report(stem)
        if c3.button("", icon=":material/close:", key=f"del_{stem}", type="tertiary", help="Delete this session"):
            st.session_state["confirm_delete"] = stem
            st.rerun()
