from __future__ import annotations

import asyncio
import json
import threading
from pathlib import Path

from topspin_review.core.progress import Progress
from topspin_review.core.stages.investigate.context import Budget, InvestigationContext


def _context(tmp_path: Path, **budget) -> tuple[InvestigationContext, Progress]:
    progress = Progress()
    ctx = InvestigationContext(
        video_path="clip.mp4",
        profile={"sport": "table tennis"},
        progress=progress,
        data_dir=tmp_path / "data",
        artifacts_dir=tmp_path / "artifacts",
        budget=Budget(**budget),
    )
    return ctx, progress


def test_run_tool_records_evidence_and_event(tmp_path) -> None:
    ctx, progress = _context(tmp_path)

    async def impl():
        return {
            "summary": "contact near 2.8s",
            "details": "elbow 122 deg",
            "times": [2.8],
            "confidence": "medium",
            "_frames": 4,
            "artifacts": ["overlay.png"],
        }

    envelope = json.loads(
        asyncio.run(ctx.run_tool("look", {"start": 2.0, "end": 3.0, "frames": 4}, window=(2.0, 3.0), impl=impl))
    )
    assert envelope["ok"] is True
    assert envelope["evidence_id"] == "ev_0001"
    assert envelope["summary"] == "contact near 2.8s"

    records = ctx.ledger.records()
    assert len(records) == 1
    assert Path(records[0].data_path).exists()
    assert ctx.coverage()["vision"] is True
    assert ctx.budget.frames == 4
    assert progress.snapshot()["events"][-1]["kind"] == "tool_finished"


def test_contexts_are_isolated(tmp_path) -> None:
    first, _ = _context(tmp_path)
    second, _ = _context(tmp_path)
    assert first.run_id != second.run_id
    assert first.report_target.artifact_dir != second.report_target.artifact_dir
    assert first.ledger is not second.ledger


def test_frame_budget_is_checked_before_tool_runs(tmp_path) -> None:
    ctx, progress = _context(tmp_path, max_frames=3)
    called = False

    def impl():
        nonlocal called
        called = True
        return {"summary": "should not run"}

    envelope = json.loads(asyncio.run(ctx.run_tool("look", {"frames": 4}, window=(0, 1), impl=impl)))
    assert called is False
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "BUDGET_EXHAUSTED"
    assert ctx.ledger.records() == []
    assert progress.snapshot()["events"][-1]["kind"] == "tool_error"


def test_cancelled_context_does_not_run_tool(tmp_path) -> None:
    cancel = threading.Event()
    cancel.set()
    progress = Progress()
    ctx = InvestigationContext(
        video_path="clip.mp4",
        profile={},
        progress=progress,
        cancel_event=cancel,
        data_dir=tmp_path / "data",
        artifacts_dir=tmp_path / "artifacts",
    )
    envelope = json.loads(
        asyncio.run(ctx.run_tool("look", {"frames": 1}, window=(0, 1), impl=lambda: {"summary": "x"}))
    )
    assert envelope["ok"] is False
    assert envelope["error"]["code"] == "CANCELLED"
    assert ctx.ledger.records() == []
