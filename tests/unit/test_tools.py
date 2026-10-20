"""Unit tests for the investigator tool layer (tools.py).

Round-3 fix B31: tools.py had zero unit test coverage. These tests exercise
the pure helpers, the validation guards in each tool, and the confidence
signal logic — all without requiring a real video file or the agent stack.
"""

from __future__ import annotations

import asyncio
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from coachme.core.stages.investigate.context import (
    Budget,
    InvestigationContext,
    InvestigationError,
)
from coachme.core.stages.investigate.tools import (
    _look,
    _pose,
    _signal_summary,
    _signal_times,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(tmp_path: Path) -> InvestigationContext:
    return InvestigationContext(
        video_path="clip.mp4",
        profile={"sport": "table tennis"},
        data_dir=tmp_path / "data",
        artifacts_dir=tmp_path / "artifacts",
    )


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_signal_summary_uses_first_two_signals() -> None:
    signals = [
        {"signal": "high elbow"},
        {"signal": "late contact"},
        {"signal": "third signal (dropped)"},
    ]
    assert _signal_summary({"signals": signals}) == "high elbow | late contact"


def test_signal_summary_falls_back_to_observations() -> None:
    parsed = {"signals": [], "observations": "No clear technique error."}
    assert _signal_summary(parsed) == "No clear technique error."


def test_signal_summary_empty_input() -> None:
    assert _signal_summary({}) == ""


def test_signal_times_extracts_and_deduplicates() -> None:
    signals = [
        {"evidence_times": [1.0, 2.5]},
        {"evidence_times": [2.5, 3.0]},
    ]
    result = _signal_times(signals)
    assert result == [1.0, 2.5, 3.0]


def test_signal_times_skips_non_numeric() -> None:
    signals = [{"evidence_times": ["bad", 1.5, None, 2.0]}]
    assert _signal_times(signals) == [1.5, 2.0]


# ---------------------------------------------------------------------------
# _look validation (raises before any I/O)
# ---------------------------------------------------------------------------


def test_look_rejects_empty_question(tmp_path) -> None:
    ctx = _ctx(tmp_path)
    with pytest.raises(InvestigationError) as exc_info:
        asyncio.run(_look(ctx, MagicMock(), 0.0, 1.0, "", 4))
    assert exc_info.value.code == "INVALID_QUESTION"


def test_look_rejects_question_over_400_chars(tmp_path) -> None:
    ctx = _ctx(tmp_path)
    with pytest.raises(InvestigationError) as exc_info:
        asyncio.run(_look(ctx, MagicMock(), 0.0, 1.0, "x" * 401, 4))
    assert exc_info.value.code == "INVALID_QUESTION"


def test_look_rejects_invalid_window(tmp_path) -> None:
    ctx = _ctx(tmp_path)
    with pytest.raises(InvestigationError) as exc_info:
        asyncio.run(_look(ctx, MagicMock(), 2.0, 1.0, "good question", 4))
    assert exc_info.value.code == "WINDOW_OUT_OF_RANGE"


def test_look_rejects_negative_start(tmp_path) -> None:
    ctx = _ctx(tmp_path)
    with pytest.raises(InvestigationError) as exc_info:
        asyncio.run(_look(ctx, MagicMock(), -1.0, 1.0, "good question", 4))
    assert exc_info.value.code == "WINDOW_OUT_OF_RANGE"


# ---------------------------------------------------------------------------
# _pose confidence signal (B27 fix verification)
# ---------------------------------------------------------------------------


def _fake_window(with_angles: bool) -> MagicMock:
    """Return a mock MeasureWindow with or without pose angle data."""
    win = MagicMock()
    win.frames = [MagicMock()]  # non-empty
    win.timestamps = [1.0]
    angles = (
        {"l_knee_mean": 142.0, "r_knee_mean": 138.0, "l_elbow_mean": 122.0, "r_elbow_mean": 119.0}
        if with_angles
        else {"l_knee_mean": None, "r_knee_mean": None, "l_elbow_mean": None, "r_elbow_mean": None}
    )
    win.measured = {
        "pose": [{"keypoints": {}}],  # non-empty — guards above pass
        "pose_summary": angles,
        "strokes": [],
        "peak_motion_time": 1.0,
    }
    return win


@patch("coachme.core.stages.investigate.tools.pose")
@patch("coachme.core.stages.investigate.tools.toolbox")
@patch("coachme.core.stages.investigate.tools.imaging")
def test_pose_confidence_high_when_angles_present(mock_imaging, mock_toolbox, mock_pose, tmp_path) -> None:
    mock_pose.available.return_value = True
    mock_pose.overlay.return_value = []  # no annotated frames → no PNG written
    mock_toolbox.measure_window.return_value = _fake_window(with_angles=True)

    ctx = _ctx(tmp_path)
    result = _pose(ctx, 0.0, 2.0, 4)
    assert result["confidence"] == "high"


@patch("coachme.core.stages.investigate.tools.pose")
@patch("coachme.core.stages.investigate.tools.toolbox")
@patch("coachme.core.stages.investigate.tools.imaging")
def test_pose_confidence_medium_when_no_angles(mock_imaging, mock_toolbox, mock_pose, tmp_path) -> None:
    mock_pose.available.return_value = True
    mock_pose.overlay.return_value = []
    mock_toolbox.measure_window.return_value = _fake_window(with_angles=False)

    ctx = _ctx(tmp_path)
    result = _pose(ctx, 0.0, 2.0, 4)
    # B27: confidence must NOT be "high" when angle readings are all None
    assert result["confidence"] == "medium"


@patch("coachme.core.stages.investigate.tools.pose")
def test_pose_raises_when_unavailable(mock_pose, tmp_path) -> None:
    mock_pose.available.return_value = False
    ctx = _ctx(tmp_path)
    with pytest.raises(InvestigationError) as exc_info:
        _pose(ctx, 0.0, 2.0, 4)
    assert exc_info.value.code == "POSE_UNAVAILABLE"


# ---------------------------------------------------------------------------
# build_tools contract
# ---------------------------------------------------------------------------


@patch("coachme.core.stages.investigate.tools.build_agent")
def test_build_tools_returns_six_callables(mock_build_agent, tmp_path) -> None:
    mock_agent = MagicMock()
    mock_agent.agent = MagicMock()
    mock_build_agent.return_value = mock_agent

    from coachme.core.stages.investigate.tools import build_tools

    ctx = _ctx(tmp_path)
    tools = build_tools(ctx)
    assert len(tools) == 6
    assert all(callable(t) for t in tools)
    names = [t.__name__ for t in tools]
    assert "get_overview" in names
    assert "look" in names
    assert "measure_motion" in names
    assert "estimate_pose" in names
    assert "get_evidence" in names
    assert "save_report" in names
