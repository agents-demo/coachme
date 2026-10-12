"""Stage helper: measure the clip (sample frames + compute metrics).

Turns a video (or a single still) into the frames and numbers the rest of the
pipeline reasons over: motion energy/shift, subject track, coarse mechanics,
optional pose and heuristic ball signal.
"""

from __future__ import annotations

from dataclasses import dataclass

from topspin_review.core import config
from topspin_review.core.progress import Progress, tick
from topspin_review.core.stages.measure import ball, sampling, strokes
from topspin_review.core.video import metrics
from topspin_review.integrations import flow, pose


@dataclass
class Measurement:
    """The result of measuring a clip."""

    meta: dict
    frames: list
    timestamps: list
    measured: dict
    is_still: bool = False


def measure(
    video_path: str,
    region_box: tuple[float, float, float, float] | None = None,
    progress: Progress | None = None,
) -> Measurement:
    """Sample the clip and measure it."""
    tick(progress, "sampling frames", 8)
    is_still = sampling.is_image(video_path)
    if is_still:
        meta, frames, timestamps = sampling.load_image(video_path)
    else:
        meta, frames, timestamps = sampling.sample_frames(video_path, config.max_frames(), config.use_cache())
    if not frames:
        raise ValueError("No frames could be extracted from the input.")

    tick(progress, "measuring motion", 20)
    steps = metrics.activity(frames, timestamps)

    # Direction-aware motion (OpenCV); its own step because it's the slowest CV pass.
    tick(progress, "measuring flow", 23)
    flow_series = flow.magnitude(frames)

    # Ball tracking is its own step: the ball is only on screen for a fraction of a
    # second, so it gets a dedicated dense pass (independent of the vision frames).
    tick(progress, "tracking ball", 26)
    if is_still:
        ball_info = ball.detect(frames, timestamps, steps)
    else:
        duration_s = float(meta.get("duration") or 0.0) or (timestamps[-1] if timestamps else 0.0)
        ball_frames, ball_times = sampling.sample_burst(
            video_path, 0.0, duration_s or 1e9, config.ball_sample_fps(), cap=config.ball_max_frames()
        )
        if len(ball_frames) >= 3:
            ball_info = ball.detect(ball_frames, ball_times, metrics.activity(ball_frames, ball_times))
        else:
            ball_info = ball.detect(frames, timestamps, steps)
    measured = metrics.analyze(frames, timestamps, ball=ball_info, region_box=region_box, with_pose=False)
    measured["flow"] = flow_series

    # Pose is its own step: it's the slowest part (mediapipe) and can be skipped.
    tick(progress, "estimating pose", 32)
    pose_seq = pose.estimate(frames)
    measured["pose"] = pose_seq
    measured["pose_summary"] = pose.summarize(pose_seq)
    measured["pose3d_summary"] = pose.summarize3d(pose_seq)
    measured["footwork"] = metrics.footwork(pose_seq)
    measured["strokes"] = strokes.segment(pose_seq, timestamps)

    return Measurement(
        meta=meta,
        frames=frames,
        timestamps=timestamps,
        measured=measured,
        is_still=is_still,
    )


__all__ = ["Measurement", "measure"]
