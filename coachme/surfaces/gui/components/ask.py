"""Floating 'ask about this report' panel — always visible, all pages, no jump."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from coachme.surfaces.gui import data

ASK_CSS = """
<style>
.st-key-askbox {
    position: fixed;
    right: 1rem;
    bottom: 1rem;
    width: 22rem;
    max-width: calc(100vw - 2rem);
    z-index: 9999;
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(128, 128, 128, 0.3);
    border-radius: 0.6rem;
    padding: 0.6rem 0.7rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}
.st-key-askbox [data-testid="stForm"] { border: none; padding: 0; }
</style>
"""


def ask_panel() -> None:
    latest = data.latest_report()
    if not latest:
        return
    stem = Path(latest.get("source", "")).stem
    key = f"qa_{stem}"
    history = st.session_state.setdefault(key, [])

    st.markdown(ASK_CSS, unsafe_allow_html=True)
    with st.container(key="askbox"):
        st.markdown("**Ask about this report**")
        for question, answer in history[-2:]:
            st.caption(f"You: {question}")
            st.markdown(f"**Coach:** {answer}")
        with st.form(key=f"ask_{stem}", clear_on_submit=True):
            question = st.text_input(
                "Your question", placeholder="e.g. How do I fix my split-step?", label_visibility="collapsed"
            )
            submitted = st.form_submit_button("Ask", use_container_width=True)
        if submitted and question:
            from coachme.core import service

            with st.spinner("Thinking…"):
                answer = service.ask_sync(stem, question)
            history.append((question, answer))
            st.rerun()
