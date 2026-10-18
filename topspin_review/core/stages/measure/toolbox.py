"""Reusable measurement primitives for fixed and investigator pipelines.

The deterministic pipeline historically did all of this in one ``measure()``
function. Investigator tools need the same operations at arbitrary intervals,
so the shared work lives here. Nothing in this module decides *what* to inspect;
that remains the caller's job.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from topspin_review.core import config
from topspin_review.core.stages.measure import sampling
from topspin_review.core.video import metrics
from topspin_review.integrations import pose


@dataclass
class Overview:
    """Cheap orientation data: metadata, sampled frames and a motion timeline."""

    meta: dict
    frames: list[Image.Image]
    timestamps: list[float]
    measured: dict

    @property
    def duration(self) -> float:
        value = self.meta.get("duration")
        if value:
            return float(value)
        return round(max(self.timestamps), 2) if self.timestamps else 0.0

    @property
    def peak_times(self) -> list[float]:
        steps = self.measured.get("activity") or []
        if not steps:
            return []
        ranked = sorted(steps, key=lambda item: float(item.get("energy") or 0.0), reverse=True)
        return [round(float(item["t"]), 2) for item in ranked[:3]]


@dataclass
class WindowMeasurement:
    """Frames and measurements for one requested interval."""

    frames: list[Image.Image]
    timestamps: list[float]
    measured: dict


def measure_frames(
    frames: list[Image.Image],
    timestamps: list[float],
    *,
    ball: dict | None = None,
    region_box: tuple[float, float, float, float] | None = None,
    with_pose: bool = True,
) -> dict:
    """Measure an already-sampled frame sequence.

    This is the canonical post-sampling stage. ``measure()`` and interval tools
    both call it so their numbers cannot drift.
    """
    measured = metrics.analyze(
        frames,
        timestamps,
        ball=ball,
        region_box=region_box,
        with_pose=False,
    )
    if with_pose:
        pose_seq = pose.estimate(frames)
        measured["pose"] = pose_seq
        measured["pose_summary"] = pose.summarize(pose_seq)
        measured["pose3d_summary"] = pose.summarize3d(pose_seq)
        measured["footwork"] = metrics.footwork(pose_seq)
        from topspin_review.core.stages.measure import strokes

        measured["strokes"] = strokes.segment(pose_seq, timestamps)
    else:
        measured["pose"] = None
        measured["pose_summary"] = {}
        measured["pose3d_summary"] = {}
        measured["footwork"] = {}
        measured["strokes"] = []
    return measured


def overview(
    video_path: str,
    *,
    max_frames: int = 32,
    use_cache: bool = True,
) -> Overview:
    """Return a cheap, motion-weighted orientation view of the clip."""
    meta, frames, timestamps = sampling.sample_frames(
        video_path,
        max(1, int(max_frames)),
        use_cache,
    )
    if not frames:
        raise ValueError("No frames could be extracted from the input.")
    steps = metrics.activity(frames, timestamps)
    measured = {"activity": steps, "peak_motion_time": _peak_time(steps)}
    return Overview(meta=meta, frames=frames, timestamps=timestamps, measured=measured)


def measure_window(
    video_path: str,
    start: float,
    end: float,
    *,
    frames: int = 8,
    region_box: tuple[float, float, float, float] | None = None,
    with_pose: bool = True,
    ball: dict | None = None,
) -> WindowMeasurement:
    """Sample and measure one interval in seconds.

    ``frames`` is clamped to the investigator's per-call ceiling. The caller is
    responsible for budgeting and for rejecting invalid windows; this helper
    keeps the video math in one place.
    """
    count = max(1, min(int(frames), int(config.investigator_max_window_frames())))
    frame_list, timestamps = sampling.sample_window(video_path, float(start), float(end), count)
    if not frame_list:
        raise ValueError(f"No frames in window [{start}, {end}].")
    measured = measure_frames(
        frame_list,
        timestamps,
        ball=ball,
        region_box=region_box,
        with_pose=with_pose,
    )
    return WindowMeasurement(frames=frame_list, timestamps=timestamps, measured=measured)


def _peak_time(steps: list[dict]) -> float | None:
    if not steps:
        return None
    return round(float(max(steps, key=lambda item: float(item.get("energy") or 0.0))["t"]), 2)


__all__ = ["Overview", "WindowMeasurement", "measure_frames", "measure_window", "overview"]
