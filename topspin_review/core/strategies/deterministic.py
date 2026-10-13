"""Deterministic analysis strategy (the default).

Measure motion, params two fixed vision passes, then have the report agent write the
report. The alternative model-driven strategy is
:mod:`topspin_review.core.strategies.agentic`.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from topspin_review.core import config
from topspin_review.core.params import Params
from topspin_review.core.progress import Progress, tick
from topspin_review.core.stages import observe
from topspin_review.core.stages.coach import retrieve_reports, verify_issues
from topspin_review.core.stages.coach.prompts import rubric_text
from topspin_review.core.stages.measure import ball, quality, sampling
from topspin_review.core.strategies.base import Strategy
from topspin_review.core.video import imaging, metrics
from topspin_review.domain import game_reading
from topspin_review.domain import report as report_schema
from topspin_review.integrations import media, pose
from topspin_review.integrations.storage import runtime, store


def _clean_windows(raw: Any, timestamps: list[float], cap: int) -> list[dict]:
    """Validate the model's requested windows into sorted [start, end] pairs."""
    end_limit = round(max(timestamps), 2) if timestamps else 0.0
    windows: list[dict] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        try:
            start = max(0.0, float(item.get("start", 0)))
            end = min(end_limit, float(item.get("end", 0)))
        except (TypeError, ValueError):
            continue
        if end - start < 0.2:
            continue
        windows.append({"start": round(start, 2), "end": round(end, 2), "why": str(item.get("why", ""))})
    return windows[:cap]


def _zoom_frames(video_path: str, windows: list[dict], budget: int) -> tuple[list, list]:
    """Sample a burst of frames inside each window, capped to ``budget`` total."""
    if not windows or budget <= 0:
        return [], []
    per = max(1, budget // len(windows))
    frames: list = []
    times: list[float] = []
    for window in windows:
        f, t = sampling.sample_burst(video_path, window["start"], window["end"], config.zoom_fps(), cap=per)
        frames.extend(f)
        times.extend(t)
    if len(frames) > budget:
        step = len(frames) / budget
        keep = sorted({int(i * step) for i in range(budget)})
        frames = [frames[i] for i in keep if i < len(frames)]
        times = [times[i] for i in keep if i < len(times)]
    return frames, times


def _save_artifacts(video_path: str, frames, timestamps, measured: dict, region_box) -> dict:
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


class DeterministicStrategy(Strategy):
    """The default: fixed measure → two-pass vision → report pipeline."""

    name = "deterministic"
    description = "Fixed pipeline: measure motion, two vision passes, then write the report."

    async def _run(self, params: Params, progress: Progress | None) -> tuple[Any, dict]:
        frames, timestamps, measured, profile = params.frames, params.timestamps, params.measured, params.profile
        clip_quality = quality.evaluate(params.meta, frames, measured)
        params.state["clip_quality"] = clip_quality

        tick(progress, "writing artifacts", 30)
        params.artifact_paths.update(_save_artifacts(params.video_path, frames, timestamps, measured, params.region_box))

        agent, media_dir = params.session.vision_agent, params.session.media_dir
        if params.is_still:
            tick(progress, "vision: reviewing image", 55)
            coarse_out = {"overall": "", "attentive_windows": [], "limitations": []}
            windows: list[dict] = []
            zoom_imgs: list = []
            zoom_times: list[float] = []
            fine_out = await observe.analyze_still(frames[0], profile, agent=agent, media_dir=media_dir)
        else:
            tick(progress, "vision: overview", 38)
            coarse_out = await observe.coarse(params.meta, frames, timestamps, measured, profile, agent=agent, media_dir=media_dir)
            windows = _clean_windows(coarse_out.get("attentive_windows"), timestamps, config.max_windows())
            tick(progress, "vision: zoom", 52)
            zoom_imgs, zoom_times = _zoom_frames(params.video_path, windows, config.zoom_frames())
            tick(progress, "vision: detail", 60)
            fine_out = await observe.fine(
                frames, timestamps, measured, windows, zoom_imgs, zoom_times, profile, agent=agent, media_dir=media_dir
            )
        observations = observe.observations_text(coarse_out, fine_out)
        params.state["observations"] = observations

        all_reports = store.get_reports()
        prev = self._previous_summary(params)
        progress_note = prev.get("text", "") if prev else "No previous report."
        repeated = ", ".join(prev.get("repeated_themes", [])) if prev else ""
        related = ""
        if config.retrieval_enabled():
            related = retrieve_reports.context_text(all_reports, f"{profile.get('goal', '')} {observations}")

        window_label = ", ".join(f"{w['start']}-{w['end']}s" for w in windows) or "none"
        rubric = rubric_text(profile.get("sport", "table tennis"))
        baseline = ""
        if all_reports:
            prev_mech = (all_reports[-1].get("metrics") or {}).get("mechanics") or {}
            now_mech = measured.get("mechanics") or {}
            if prev_mech or now_mech:
                deltas = {
                    k: round(float(now_mech.get(k, 0)) - float(prev_mech.get(k, 0)), 3)
                    for k in set(prev_mech) | set(now_mech)
                }
                baseline = f"Previous mechanics: {prev_mech}\nNow: {now_mech}\nChange: {deltas}"
        quality_note = "; ".join(clip_quality.get("warnings") or []) or "ok"
        reading = game_reading.summarize(measured)

        query = (
            f"Today is {date.today().isoformat()}. "
            f"Write my coaching report for a {profile.get('sport', 'table tennis')} session.\n"
            f"Player: {self._profile_line(params)}.\n\n"
            f"History: {progress_note}" + (f" Recurring themes: {repeated}." if repeated else "") + "\n"
            + (f"Related past sessions:\n{related}\n" if related else "")
            + "\n"
            f"Analysis ({len(frames)} sampled frames, windows examined: {window_label}):\n"
            f"{observations}\n\n"
            f"Measured motion/mechanics:\n{metrics.text(measured)}\n\n"
            f"Game reading (those measurements read in {profile.get('sport', 'table tennis')} terms):\n{reading['text']}\n\n"
            f"Footage quality: {quality_note}.\n\n"
            + (f"Baseline (previous session):\n{baseline}\n\n" if baseline else "")
            + f"Check the player against this technique rubric (issues should map to it):\n{rubric}\n\n"
            "Save the report with save_report (schema with evidence_times and confidence), "
            "then give me a short summary."
        )
        result = await self._run_report_agent(
            params, self._build_report_agent(params), query, progress, stage="agent writing report", pct=80
        )
        return result, {
            "observations": observations,
            "windows": windows,
            "signals": fine_out.get("signals") or [],
        }

    async def _after_report(self, params: Params, report: dict, progress: Progress | None) -> dict:
        clip_quality = params.state["clip_quality"]
        tick(progress, "verifying", 95)
        report_schema.calibrate(report, clip_quality)
        if config.verify_reports():
            try:
                await verify_issues.verify(
                    report, params.state["observations"], metrics.text(params.measured), recorder=params.session.recorder
                )
            except Exception:
                pass

        clips: dict = {}
        if config.clips_enabled() and not params.is_still:
            # Cut around the CV-derived moments (agent-free), not the report's issues.
            reading = game_reading.summarize(params.measured)
            clip_times = [m["t"] for m in reading.get("moments", [])][:3]
            try:
                clips = media.make_clips(params.video_path, clip_times, Path(params.video_path).stem)
            except Exception:
                clips = {}

        limitations = list(report.get("limitations") or []) + list(clip_quality.get("warnings") or [])
        return {"quality": clip_quality, "clips": clips, "limitations": limitations}
