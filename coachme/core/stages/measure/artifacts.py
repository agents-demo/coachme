"""Shared artifact writer for all analysis modes."""

from __future__ import annotations

import json
from pathlib import Path

from coachme.core.stages.measure import ball
from coachme.core.video import imaging, metrics
from coachme.integrations import pose
from coachme.integrations.storage import runtime


def save_artifacts(video_path: str, frames, timestamps, measured: dict, region_box) -> dict:
    """Save the contact sheet, motion map, pose overlay and metrics; return their paths."""
    stem = Path(video_path).stem
    paths: dict[str, str] = {}

    sheet = imaging.contact_sheet(frames, timestamps, cols=min(4, len(frames)))
    sheet_path = runtime.ARTIFACTS_DIR / f"{stem}_frames.png"
    imaging.save_png(sheet, sheet_path)
    paths["frames"] = str(sheet_path)

    mask = metrics.region_from_box(region_box) if region_box else metrics.subject_region(frames)
    motion_map = metrics.motion_map(frames, mask=mask)
    if motion_map is not None:
        motion_path = runtime.ARTIFACTS_DIR / f"{stem}_motion.png"
        imaging.save_png(motion_map, motion_path)
        paths["motion"] = str(motion_path)

    # Footwork heat map: where the subject spent the most time (from the subject track).
    heat = metrics.position_heatmap(frames, measured.get("track") or [])
    if heat is not None:
        heat_path = runtime.ARTIFACTS_DIR / f"{stem}_heatmap.png"
        imaging.save_png(heat, heat_path)
        paths["heatmap"] = str(heat_path)

    # Ball path overlay (heuristic) — where the tracked ball moved.
    ball_img = ball.overlay(frames, measured.get("ball") or {})
    if ball_img is not None:
        ball_path = runtime.ARTIFACTS_DIR / f"{stem}_ball.png"
        imaging.save_png(ball_img, ball_path)
        paths["ball"] = str(ball_path)

    if measured.get("pose"):
        annotated = pose.overlay(frames, measured["pose"])
        if annotated:
            # One full-size annotated frame at the peak-motion moment (a big, clear pose image).
            peak_t = measured.get("peak_motion_time")
            hero_idx = 0
            if peak_t is not None and timestamps:
                hero_idx = min(range(len(timestamps)), key=lambda k: abs(timestamps[k] - peak_t))
            hero_path = runtime.ARTIFACTS_DIR / f"{stem}_pose_hero.png"
            imaging.save_png(annotated[hero_idx], hero_path)
            paths["pose_hero"] = str(hero_path)

            pose_sheet = imaging.contact_sheet(annotated, timestamps, cols=min(4, len(annotated)))
            pose_path = runtime.ARTIFACTS_DIR / f"{stem}_pose.png"
            imaging.save_png(pose_sheet, pose_path)
            paths["pose"] = str(pose_path)

    metrics_path = runtime.ARTIFACTS_DIR / f"{stem}_metrics.json"
    metrics_path.write_text(json.dumps(measured, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["metrics"] = str(metrics_path)
    return paths

