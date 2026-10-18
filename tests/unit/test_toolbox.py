from __future__ import annotations

import imageio.v2 as imageio
import numpy as np
from PIL import Image

from topspin_review.core.stages.measure import toolbox
from topspin_review.core.video import metrics


def _frames(n: int = 6) -> tuple[list[Image.Image], list[float]]:
    frames = []
    times = []
    for i in range(n):
        arr = np.zeros((120, 160, 3), dtype=np.uint8)
        arr[:, :, 0] = 20 + i * 10
        # A moving bright block gives the activity/track code something real.
        x = 20 + i * 8
        arr[30:90, x : x + 30] = 220
        frames.append(Image.fromarray(arr))
        times.append(i / 10)
    return frames, times


def test_measure_frames_matches_metrics_analyze_without_pose() -> None:
    frames, times = _frames()
    expected = metrics.analyze(frames, times, with_pose=False)
    actual = toolbox.measure_frames(frames, times, with_pose=False)

    for key in (
        "activity",
        "track",
        "posture",
        "mechanics",
        "footwork_series",
        "calibration",
        "calibrated",
        "subject_coverage",
        "peak_motion_time",
        "mean_energy",
        "max_energy",
        "net_shift",
    ):
        assert actual[key] == expected[key], key
    assert actual["pose"] is None
    assert actual["strokes"] == []


def test_measure_window_stays_inside_requested_interval(tmp_path) -> None:
    path = tmp_path / "clip.mp4"
    frames, _ = _frames(10)
    writer = imageio.get_writer(str(path), fps=10, macro_block_size=None)
    try:
        for frame in frames:
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()

    window = toolbox.measure_window(str(path), 0.2, 0.8, frames=4, with_pose=False)
    assert window.frames
    assert len(window.frames) == len(window.timestamps)
    assert all(0.1 <= t <= 0.9 for t in window.timestamps)
    assert "activity" in window.measured
    assert window.measured["pose"] is None


def test_overview_reports_peaks(tmp_path) -> None:
    path = tmp_path / "clip.mp4"
    frames, _ = _frames(10)
    writer = imageio.get_writer(str(path), fps=10, macro_block_size=None)
    try:
        for frame in frames:
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()

    overview = toolbox.overview(str(path), max_frames=8, use_cache=False)
    assert overview.frames
    assert overview.timestamps
    assert overview.peak_times
    assert overview.duration > 0
