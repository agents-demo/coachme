"""Read-side helpers for the UI: the latest report and footage checks."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from coachme.integrations.storage import store

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}


def latest_report() -> dict:
    reports = store.get_reports()
    latest = store.find_report(st.session_state.get("latest_stem", "")) if st.session_state.get("latest_stem") else None
    if latest is None:
        getter = getattr(store, "latest_report", None)
        latest = (getter() if callable(getter) else None) or (reports[-1] if reports else {})
    return latest


def video_info(path: str) -> dict:
    try:
        import imageio

        reader = imageio.get_reader(str(path), format="ffmpeg")
        meta = dict(reader.get_meta_data())
        reader.close()
        return {"fps": meta.get("fps"), "duration": meta.get("duration"), "size": meta.get("size")}
    except Exception:
        return {}


def footage_check(path: str) -> None:
    if Path(path).suffix.lower() in IMAGE_EXTS:
        st.info("Single photo: you'll get feedback on your **posture**, not movement or footwork.")
        return
    info = video_info(path)
    if not info:
        return
    size = info.get("size") or (0, 0)
    fps = info.get("fps") or 0
    duration = info.get("duration") or 0
    notes = []
    if duration and duration < 3:
        notes.append("very short (a few rallies are better)")
    if fps and fps < 25:
        notes.append(f"low frame rate ({fps:.0f} fps — 60+ shows footwork better)")
    if size and size[1] and size[1] < 480:
        notes.append("low resolution")
    if notes:
        st.warning("Footage tips: " + "; ".join(notes) + ". Side-on, full-body works best.")
    else:
        st.success("Looks good — analyzing this should give useful feedback.")
