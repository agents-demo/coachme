"""The investigator's MVP tool surface.

Tools are thin closures over one :class:`InvestigationContext`. Every successful
measurement/inspection goes through ``ctx.run_tool`` so evidence and budgets are
recorded in one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from topspin_review.core import config
from topspin_review.core.stages.investigate.context import InvestigationContext, InvestigationError
from topspin_review.core.stages.measure import sampling, toolbox
from topspin_review.core.stages.observe import render_images
from topspin_review.core.stages.observe.build_agent import build_agent
from topspin_review.core.stages.observe.inspect import INSPECT_SYSTEM, inspect
from topspin_review.core.video import imaging, metrics
from topspin_review.integrations import pose


def build_tools(ctx: InvestigationContext) -> list:
    """Build the six MVP tools bound to one run context."""
    inspector = build_agent(
        media_dir=str(ctx.media_dir),
        workspace=str(ctx.workspace_dir),
        max_iterations=3,
        system_prompt=INSPECT_SYSTEM,
    ).agent

    async def get_overview() -> str:
        """Return the clip duration, motion peaks and a contact sheet path."""
        return await ctx.run_tool(
            "get_overview",
            {},
            window=None,
            impl=lambda: _overview(ctx),
        )

    async def look(start: float, end: float, question: str, frames: int = 4) -> str:
        """Inspect a time window with the vision model and return observations.

        Args:
            start: Window start in seconds.
            end: Window end in seconds.
            question: Focused question about the window (max 400 chars).
            frames: Frames to sample (1-12).
        """
        return await ctx.run_tool(
            "look",
            {"start": start, "end": end, "question": question, "frames": frames},
            window=(float(start), float(end)),
            impl=lambda: _look(ctx, inspector, start, end, question, frames),
        )

    async def measure_motion(start: float, end: float, frames: int = 8) -> str:
        """Measure motion, subject tracking and mechanics in a window.

        Args:
            start: Window start in seconds.
            end: Window end in seconds.
            frames: Frames to sample (1-8).
        """
        return await ctx.run_tool(
            "measure_motion",
            {"start": start, "end": end, "frames": frames},
            window=(float(start), float(end)),
            impl=lambda: _motion(ctx, start, end, frames),
        )

    async def estimate_pose(start: float, end: float, frames: int = 8) -> str:
        """Estimate pose, joint angles and wrist-speed events in a window.

        Args:
            start: Window start in seconds.
            end: Window end in seconds.
            frames: Frames to sample (1-8).
        """
        return await ctx.run_tool(
            "estimate_pose",
            {"start": start, "end": end, "frames": frames},
            window=(float(start), float(end)),
            impl=lambda: _pose(ctx, start, end, frames),
        )

    def get_evidence(evidence_id: str) -> str:
        """Return the compact record and details for one evidence ID."""
        return ctx.get_evidence(str(evidence_id))

    def save_report(report_json: str) -> str:
        """Save the coaching report after evidence validation.

        Args:
            report_json: JSON object with issues, evidence_ids, coverage and
                investigation metadata.
        """
        return ctx.save_report(report_json)

    return [get_overview, look, measure_motion, estimate_pose, get_evidence, save_report]


def _overview(ctx: InvestigationContext) -> dict[str, Any]:
    view = toolbox.overview(ctx.video_path, max_frames=32, use_cache=True)
    sheet = render_images.overview_sheet(view.frames, view.timestamps, ctx.media_dir)
    steps = view.measured.get("activity") or []
    return {
        "summary": (
            f"{view.duration:.1f}s clip; motion peaks at "
            f"{', '.join(str(t) for t in view.peak_times) or 'unknown'}"
        ),
        "duration": view.duration,
        "fps": view.meta.get("fps"),
        "size": view.meta.get("size"),
        "is_still": sampling.is_image(ctx.video_path),
        "peak_times": view.peak_times,
        "activity": steps[:40],
        "times": view.peak_times,
        "confidence": "high" if steps else "low",
        "artifacts": [sheet],
        "_frames": len(view.frames),
    }


async def _look(
    ctx: InvestigationContext,
    inspector: Any,
    start: float,
    end: float,
    question: str,
    frames: int,
) -> dict[str, Any]:
    if not str(question or "").strip():
        raise InvestigationError("INVALID_QUESTION", "question must not be empty")
    if len(str(question)) > 400:
        raise InvestigationError("INVALID_QUESTION", "question is limited to 400 characters")
    if start < 0 or end <= start:
        raise InvestigationError("WINDOW_OUT_OF_RANGE", f"invalid window [{start}, {end}]")
    if end - start > config.investigator_max_window_seconds():
        raise InvestigationError("WINDOW_TOO_LONG", "window exceeds the maximum length")
    count = max(1, min(int(frames), config.investigator_max_window_frames()))
    frame_list, times = sampling.sample_window(ctx.video_path, float(start), float(end), count)
    if not frame_list:
        raise InvestigationError("NO_FRAMES", f"no frames in window [{start}, {end}]")
    parsed = await inspect(
        inspector,
        frame_list,
        times,
        str(question),
        ctx.profile,
        media_dir=ctx.media_dir,
        start=float(start),
        end=float(end),
    )
    signals = parsed.get("signals") or []
    confidence = min(
        (item.get("confidence", "low") for item in signals),
        key=lambda value: {"low": 0, "medium": 1, "high": 2}.get(value, 0),
        default="low",
    )
    return {
        "summary": _signal_summary(parsed),
        "details": parsed.get("observations") or "",
        "observations": parsed.get("observations") or "",
        "signals": signals,
        "limitations": parsed.get("limitations") or [],
        "times": _signal_times(signals),
        "confidence": confidence,
        "artifacts": [parsed["sheet_path"]] if parsed.get("sheet_path") else [],
        "_frames": len(frame_list),
    }


def _motion(ctx: InvestigationContext, start: float, end: float, frames: int) -> dict[str, Any]:
    window = toolbox.measure_window(
        ctx.video_path,
        start,
        end,
        frames=frames,
        with_pose=False,
    )
    measured = window.measured
    peak = measured.get("peak_motion_time")
    mechanics = measured.get("mechanics") or {}
    return {
        "summary": (
            f"mean energy {measured.get('mean_energy')}, peak at {peak}s, "
            f"lower range {mechanics.get('lower_lateral_range')}"
        ),
        "details": metrics.text(measured)[:2000],
        "times": [peak] if peak is not None else [],
        "confidence": "high" if window.frames else "low",
        "artifacts": [],
        "_frames": len(window.frames),
    }


def _pose(ctx: InvestigationContext, start: float, end: float, frames: int) -> dict[str, Any]:
    if not pose.available():
        raise InvestigationError("POSE_UNAVAILABLE", "pose estimation is not available")
    window = toolbox.measure_window(
        ctx.video_path,
        start,
        end,
        frames=frames,
        with_pose=True,
    )
    measured = window.measured
    sequence = measured.get("pose") or []
    if not sequence:
        raise InvestigationError("POSE_UNAVAILABLE", "no usable pose in this window")
    summary = measured.get("pose_summary") or {}
    strokes = measured.get("strokes") or []
    peak = measured.get("peak_motion_time")
    paths: list[str] = []
    annotated = pose.overlay(window.frames, sequence)
    if annotated:
        index = 0
        if peak is not None and window.timestamps:
            index = min(
                range(len(window.timestamps)),
                key=lambda i: abs(window.timestamps[i] - peak),
            )
        path = Path(ctx.media_dir) / f"pose_{int(round(start * 1000))}_{int(round(end * 1000))}.png"
        imaging.save_png(annotated[index], path)
        paths.append(str(path))
    return {
        "summary": (
            f"knee {summary.get('l_knee_mean')}/{summary.get('r_knee_mean')}, "
            f"elbow {summary.get('l_elbow_mean')}/{summary.get('r_elbow_mean')}, "
            f"{len(strokes)} wrist event(s)"
        ),
        "details": metrics.text(measured)[:2000],
        "times": [event["t"] for event in strokes] or ([peak] if peak is not None else []),
        "confidence": "high" if sequence else "low",
        "artifacts": paths,
        "_frames": len(window.frames),
    }


def _signal_summary(parsed: dict) -> str:
    signals = parsed.get("signals") or []
    if signals:
        return " | ".join(str(item.get("signal", "")) for item in signals[:2])
    return str(parsed.get("observations") or "")[:500]


def _signal_times(signals: list[dict]) -> list[float]:
    out: list[float] = []
    for signal in signals:
        for value in signal.get("evidence_times") or []:
            try:
                out.append(round(float(value), 2))
            except (TypeError, ValueError):
                continue
    return sorted(set(out))


__all__ = ["build_tools"]
