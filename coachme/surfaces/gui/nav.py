"""Page registry and navigation helpers.

``PAGE_OBJS`` is populated by :mod:`coachme.surfaces.gui.ui` after it
builds the ``st.Page`` objects; page modules import :func:`go` / :func:`open_report`
rather than the objects themselves, so there is no import cycle.
"""

from __future__ import annotations

import streamlit as st

PAGE_OBJS: dict = {}


def go(page: str) -> None:
    st.switch_page(PAGE_OBJS[page])


def open_report(stem: str) -> None:
    st.session_state["latest_stem"] = stem
    st.session_state["seek"] = 0.0
    go("Result")
