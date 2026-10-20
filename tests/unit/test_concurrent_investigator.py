"""Two concurrent InvestigationContext instances must share no state.

Every ledger, budget, run_id and artifact path must be fully isolated
even when tool calls happen simultaneously from two threads.
"""
from __future__ import annotations

import asyncio
import threading
from pathlib import Path

from coachme.core.stages.investigate.context import Budget, InvestigationContext


def _ctx(tmp_path: Path, name: str, max_calls: int = 8) -> InvestigationContext:
    return InvestigationContext(
        video_path=f"{name}.mp4",
        profile={"sport": "table tennis"},
        data_dir=tmp_path / name / "data",
        artifacts_dir=tmp_path / name / "artifacts",
        budget=Budget(max_tool_calls=max_calls, max_frames=40),
    )


def _add(ctx: InvestigationContext, summary: str) -> None:
    async def _impl():
        return {"summary": summary, "times": [], "confidence": "low"}

    asyncio.run(
        ctx.run_tool("look", {"frames": 1}, window=(0.0, 1.0), impl=_impl)
    )


# ── serial isolation ────────────────────────────────────────────────────────


def test_two_contexts_have_isolated_ledgers(tmp_path: Path) -> None:
    ctx_a = _ctx(tmp_path, "a")
    ctx_b = _ctx(tmp_path, "b")

    _add(ctx_a, "finding in A")
    _add(ctx_b, "finding in B")

    records_a = ctx_a.ledger.records()
    records_b = ctx_b.ledger.records()

    assert len(records_a) == 1
    assert len(records_b) == 1
    # Each ledger starts its counter from 1 independently.
    assert records_a[0].id == "ev_0001"
    assert records_b[0].id == "ev_0001"
    assert records_a[0].summary == "finding in A"
    assert records_b[0].summary == "finding in B"


def test_run_ids_are_unique(tmp_path: Path) -> None:
    ctx_a = _ctx(tmp_path, "x")
    ctx_b = _ctx(tmp_path, "y")
    assert ctx_a.run_id != ctx_b.run_id


def test_artifact_dirs_are_unique(tmp_path: Path) -> None:
    ctx_a = _ctx(tmp_path, "p")
    ctx_b = _ctx(tmp_path, "q")
    assert ctx_a.report_target.artifact_dir != ctx_b.report_target.artifact_dir


def test_evidence_run_ids_match_context(tmp_path: Path) -> None:
    ctx = _ctx(tmp_path, "r")
    _add(ctx, "some finding")
    record = ctx.ledger.records()[0]
    assert record.run_id == ctx.run_id


# ── concurrent isolation ────────────────────────────────────────────────────


def test_concurrent_tool_calls_do_not_cross_ledgers(tmp_path: Path) -> None:
    """Two threads each running 4 tool calls must end up with 4 records each."""
    ctx_a = _ctx(tmp_path, "ca", max_calls=10)
    ctx_b = _ctx(tmp_path, "cb", max_calls=10)
    errors: list[Exception] = []

    def run_a() -> None:
        try:
            for i in range(4):
                _add(ctx_a, f"a_{i}")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    def run_b() -> None:
        try:
            for i in range(4):
                _add(ctx_b, f"b_{i}")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    t_a = threading.Thread(target=run_a)
    t_b = threading.Thread(target=run_b)
    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    assert not errors, f"Errors in threads: {errors}"
    assert len(ctx_a.ledger.records()) == 4
    assert len(ctx_b.ledger.records()) == 4

    for rec in ctx_a.ledger.records():
        assert rec.run_id == ctx_a.run_id
    for rec in ctx_b.ledger.records():
        assert rec.run_id == ctx_b.run_id
