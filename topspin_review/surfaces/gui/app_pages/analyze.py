"""Page: Analyze."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from topspin_review.integrations.storage import runtime
from topspin_review.surfaces.gui import data, style
from topspin_review.surfaces.gui.job import prelude, start_worker


def page() -> None:
    prelude()
    style.hero(
        "Analyze a video or photo",
        "A few rallies from the side (full body) gives the most; a single photo gives posture feedback.",
    )

    uploaded = st.file_uploader(
        "Choose a video or a single photo", type=["mp4", "mov", "avi", "mkv", "png", "jpg", "jpeg", "bmp", "webp"]
    )
    use_sample = st.checkbox("…or use the built-in sample clip")

    target: Path | None = None
    if uploaded is not None:
        target = runtime.DATA_DIR / f"upload_{uploaded.name}"
    elif use_sample:
        target = runtime.DATA_DIR / "sample.mp4"
    if target is not None:
        data.footage_check(str(target))

    with st.expander("Advanced"):
        st.checkbox("Let the AI decide what to review (slower)", key="_agentic")
        st.slider("How much of the video to study", 4, 30, value=12, key="_frames")
        st.number_input("Only study the first N seconds (0 = all)", 0, 3600, value=0, key="_seconds")
        if st.checkbox("Only look at me (ignore other people)", key="_use_box"):
            st.session_state["_box"] = (
                st.slider("left", 0.0, 1.0, 0.0, 0.05, key="_left"),
                st.slider("top", 0.0, 1.0, 0.0, 0.05, key="_top"),
                st.slider("right", 0.0, 1.0, 1.0, 0.05, key="_right"),
                st.slider("bottom", 0.0, 1.0, 1.0, 0.05, key="_bottom"),
            )
        else:
            st.session_state["_box"] = None

    os.environ["VISION_MAX_FRAMES"] = str(int(st.session_state.get("_frames", 12)))
    os.environ["VISION_MAX_SECONDS"] = str(int(st.session_state.get("_seconds", 0)))

    if st.button("Analyze", type="primary", disabled="job" in st.session_state):
        if target is None:
            st.warning("Choose a video or photo (or tick the sample clip).")
        else:
            if uploaded is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(uploaded.getbuffer())
            if not target.exists():
                st.error(f"File not found: {target}")
            else:
                start_worker(
                    target,
                    agentic=bool(st.session_state.get("_agentic")),
                    box=st.session_state.get("_box"),
                )
                st.rerun()
