"""Page: Result (report, movement, details, technical)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from coachme.domain import evaluate, render
from coachme.integrations import reporting as export
from coachme.surfaces.gui import data, nav, style
from coachme.surfaces.gui.components import ask, execution
from coachme.surfaces.gui.job import prelude


def _moment_row(parent, idx: int, issue: dict) -> None:
    parent.markdown(f"- {issue.get('issue', '')}")
    times = issue.get("evidence_times") or []
    if times:
        cols = parent.columns(len(times))
        for c, t in zip(cols, times):
            if c.button(f"▶ {t}s", key=f"seek_{idx}_{t}"):
                st.session_state.seek = float(t)
                st.rerun()


def page() -> None:
    prelude()
    latest = data.latest_report()
    if not latest:
        st.info("No report yet.")
        if st.button("Analyze a video or photo", type="primary"):
            nav.go("Analyze")
        return

    style.hero(render.video_name(latest), f"{latest.get('sport', '')} · {latest.get('date', '')}")

    tab_report, tab_movement, tab_details, tab_technical = st.tabs(["Report", "Movement", "Details", "Technical"])

    with tab_report:
        if latest.get("focus"):
            st.success(f"**Focus next session:** {latest['focus']}")
        if latest.get("summary"):
            st.write(latest["summary"])

        src = latest.get("source")
        seek = float(st.session_state.get("seek", 0.0) or 0.0)
        if src and Path(src).exists():
            if src.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                st.image(src)
            else:
                try:
                    st.video(src, start_time=int(round(seek)))
                except TypeError:
                    st.video(src)
        else:
            st.caption("(media not found)")

        strengths = latest.get("strengths") or []
        if strengths:
            st.markdown("#### What's working")
            for item in strengths:
                st.markdown(f"- {item}")

        issues = latest.get("issues") or []
        if issues:
            st.markdown("#### What to fix")
            st.caption("Tap a time to jump the video to that moment.")
            for idx, item in enumerate(issues):
                if isinstance(item, dict):
                    _moment_row(st, idx, item)
                else:
                    st.markdown(f"- {item}")

        clips = latest.get("clips") or {}
        if clips:
            with st.expander("Watch the key moments"):
                for t, path in clips.items():
                    st.markdown(f"**Around {t}s**")
                    if Path(path).exists():
                        st.video(path)

        drills = latest.get("drills") or []
        if drills:
            st.markdown("#### Drills to practice")
            for item in drills:
                st.markdown(f"- {item}")
            if st.button("Add these drills to Practice"):
                nav.go("Practice")

        if latest.get("progress"):
            st.info(f"Since last time: {latest['progress']}")

    with tab_movement:
        metrics = latest.get("metrics") or {}
        artifacts = latest.get("artifacts") or {}
        if not metrics or not (metrics.get("activity")):
            st.info("No movement data (single-image inputs have none).")
        else:
            import pandas as pd

            df = pd.DataFrame(
                {"movement": [s["energy"] for s in metrics["activity"]]},
                index=[round(s["t"], 2) for s in metrics["activity"]],
            )
            df.index.name = "seconds"
            st.line_chart(df, y_label="movement")
            st.caption(
                "How much the picture changed at each moment: a spike is a step or a swing, "
                "a flat stretch is little movement."
            )
            if metrics.get("peak_motion_time") is not None:
                st.caption(f"Biggest movement around t={metrics['peak_motion_time']}s.")
        mpath = artifacts.get("motion")
        if mpath and Path(mpath).exists():
            st.image(mpath, caption="Red = where you moved most during the clip.")
        with st.expander("Frames we looked at"):
            fpath = artifacts.get("frames")
            if fpath and Path(fpath).exists():
                st.image(fpath)
            ppath = artifacts.get("pose")
            if ppath and Path(ppath).exists():
                st.image(ppath, caption="Body pose overlay")

    with tab_details:
        with st.expander("Keep in mind", expanded=True):
            for item in latest.get("limitations") or []:
                st.markdown(f"- {item}")
        quality = evaluate.score(latest)
        st.write(f"Report confidence score: {quality['score']}/100")
        stem = Path(latest.get("source", "report")).stem
        st.download_button(
            "Download report (Markdown)", export.to_markdown(latest), file_name=f"{stem}_report.md", mime="text/markdown"
        )
        st.download_button(
            "Download report (HTML)", export.to_html(latest), file_name=f"{stem}_report.html", mime="text/html"
        )

    with tab_technical:
        execution.render_technical(latest)

    ask.ask_panel()
