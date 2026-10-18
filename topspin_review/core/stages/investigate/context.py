"""Per-run state for the investigator mode.

The context owns paths, budgets, cancellation, the evidence ledger and the tool
execution wrapper. It deliberately has no module-global state: two runs can be
constructed in the same process without sharing evidence or counters.
"""

from __future__ import annotations

import inspect
import json
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topspin_review.core import config
from topspin_review.core.progress import Progress
from topspin_review.core.stages.investigate.ledger import EvidenceLedger
from topspin_review.integrations.storage import runtime


class InvestigationError(RuntimeError):
    """A structured, model-visible tool error."""

    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def envelope(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "retryable": self.retryable,
            },
        }


class BudgetExceeded(InvestigationError):
    def __init__(self, message: str) -> None:
        super().__init__("BUDGET_EXHAUSTED", message, retryable=False)


class Cancelled(InvestigationError):
    def __init__(self, message: str = "run cancelled") -> None:
        super().__init__("CANCELLED", message, retryable=False)


@dataclass(frozen=True)
class ReportTarget:
    """Where a run writes its working report and its published report."""

    stem: str
    run_id: str
    working_report: Path
    final_report: Path
    artifact_dir: Path


class Budget:
    """Hard limits for one investigator run."""

    def __init__(
        self,
        *,
        max_tool_calls: int | None = None,
        max_seconds: float | None = None,
        max_tokens: int | None = None,
        max_frames: int | None = None,
    ) -> None:
        self.max_tool_calls = int(
            config.investigator_max_tool_calls() if max_tool_calls is None else max_tool_calls
        )
        self.max_seconds = float(
            config.investigator_max_seconds() if max_seconds is None else max_seconds
        )
        self.max_tokens = int(
            config.investigator_max_tokens() if max_tokens is None else max_tokens
        )
        self.max_frames = int(
            config.investigator_max_frames() if max_frames is None else max_frames
        )
        self.tool_calls = 0
        self.frames = 0
        self.seconds = 0.0
        self.tokens = 0
        self._started = time.monotonic()
        self._lock = threading.Lock()

    def check_tool_call(self) -> None:
        if self.tool_calls >= self.max_tool_calls:
            raise BudgetExceeded(f"tool-call budget exhausted ({self.max_tool_calls})")

    def check_frames(self, requested: int) -> None:
        if requested < 0:
            raise InvestigationError("INVALID_FRAMES", "frames must be >= 0")
        if self.frames + requested > self.max_frames:
            raise BudgetExceeded(
                f"frame budget exhausted (would use {self.frames + requested}/{self.max_frames})"
            )

    def check_cancel(self, cancel_event: threading.Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise Cancelled()

    def consume_tool(self, *, seconds: float, frames: int = 0) -> None:
        with self._lock:
            self.tool_calls += 1
            self.frames += max(0, int(frames))
            self.seconds += max(0.0, float(seconds))

    def elapsed(self) -> float:
        return max(0.0, time.monotonic() - self._started)

    def warning(self) -> bool:
        return bool(
            self.tool_calls >= self.max_tool_calls * 0.8
            or self.frames >= self.max_frames * 0.8
            or self.elapsed() >= self.max_seconds * 0.8
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "tool_calls": self.tool_calls,
            "max_tool_calls": self.max_tool_calls,
            "frames": self.frames,
            "max_frames": self.max_frames,
            "seconds": round(self.elapsed(), 2),
            "max_seconds": self.max_seconds,
            "tokens": self.tokens,
            "max_tokens": self.max_tokens,
        }


class InvestigationContext:
    """All mutable state for one investigator run."""

    def __init__(
        self,
        *,
        video_path: str,
        profile: dict[str, Any],
        language: str = "en",
        progress: Progress | None = None,
        cancel_event: threading.Event | None = None,
        budget: Budget | None = None,
        run_id: str | None = None,
        data_dir: Path | None = None,
        artifacts_dir: Path | None = None,
    ) -> None:
        stem = Path(video_path).stem
        self.video_path = video_path
        self.profile = dict(profile or {})
        self.language = language
        self.progress = progress
        self.cancel_event = cancel_event
        self.budget = budget or Budget()
        self.run_id = run_id or new_run_id()
        self.data_dir = Path(data_dir or runtime.DATA_DIR)
        self.artifacts_dir = Path(artifacts_dir or runtime.ARTIFACTS_DIR)

        working_root = self.data_dir / ".runs" / self.run_id
        working_root.mkdir(parents=True, exist_ok=True)
        working_report = working_root / f"{stem}_report.json"
        final_report = self.data_dir / f"{stem}_report.json"
        artifact_dir = self.artifacts_dir / f"{stem}_investigation" / self.run_id
        self.workspace_dir = artifact_dir / "workspace"
        self.media_dir = self.workspace_dir / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

        self.report_target = ReportTarget(
            stem=stem,
            run_id=self.run_id,
            working_report=working_report,
            final_report=final_report,
            artifact_dir=artifact_dir,
        )
        self.ledger = EvidenceLedger(artifact_dir, self.run_id)
        self.allow_partial = False
        self.saved = False
        self.saved_report: dict[str, Any] | None = None

    def check_cancel(self) -> None:
        self.budget.check_cancel(self.cancel_event)

    def emit(self, kind: str, **payload: Any) -> None:
        if self.progress is None:
            return
        try:
            self.progress.event(kind, **payload)
        except Exception:
            pass

    async def run_tool(
        self,
        name: str,
        args: dict[str, Any] | None,
        *,
        window: tuple[float, float] | None,
        impl: Callable[[], Any],
    ) -> str:
        """Execute one tool, record evidence and return a JSON envelope."""
        args = dict(args or {})
        started: float | None = None
        try:
            self.check_cancel()
            self.budget.check_tool_call()
            self.budget.check_frames(int(args.get("frames") or 0))
            self.emit("tool_started", tool=name, args=args)
            started = time.monotonic()
            result = impl()
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                result = {"summary": str(result)}
            record = self.ledger.add(
                tool=name,
                args=args,
                window=window,
                result=result,
                seconds=time.monotonic() - started,
                confidence=result.get("confidence"),
            )
            self.budget.consume_tool(
                seconds=time.monotonic() - started,
                frames=int(result.get("_frames") or args.get("frames") or 0),
            )
            self.emit(
                "tool_finished",
                tool=name,
                evidence_id=record.id,
                summary=record.summary,
                seconds=record.seconds,
            )
            return json.dumps(record.envelope(), ensure_ascii=False)
        except InvestigationError as exc:
            if started is not None:
                self.budget.consume_tool(seconds=time.monotonic() - started)
            self.emit("tool_error", tool=name, error=exc.code, message=exc.message)
            return json.dumps(exc.envelope(), ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            if started is not None:
                self.budget.consume_tool(seconds=time.monotonic() - started)
            self.emit("tool_error", tool=name, error="TOOL_FAILED", message=str(exc))
            return json.dumps(
                InvestigationError("TOOL_FAILED", str(exc), retryable=False).envelope(),
                ensure_ascii=False,
            )

    def save_report(self, report_json: str) -> str:
        """Validate and save the report to this run's working target."""
        from topspin_review.core.stages.coach import report_tools

        if self.saved:
            return json.dumps(
                InvestigationError("REPORT_ALREADY_SAVED", "report already saved").envelope(),
                ensure_ascii=False,
            )
        result = report_tools.save_report_result(
            report_json,
            target=self.report_target.working_report,
            evidence_records=self.ledger.records(),
            allow_partial=self.allow_partial,
        )
        if result.get("ok"):
            self.saved = True
            self.saved_report = result.get("report")
            self.emit("report_saved", path=result.get("report_path"))
        return json.dumps(result, ensure_ascii=False)

    def get_evidence(self, evidence_id: str) -> str:
        record = self.ledger.get(evidence_id)
        if record is None:
            return json.dumps(
                InvestigationError("UNKNOWN_EVIDENCE", f"unknown evidence: {evidence_id}").envelope(),
                ensure_ascii=False,
            )
        return json.dumps(record.to_dict(), ensure_ascii=False)

    def coverage(self) -> dict[str, bool]:
        return self.ledger.coverage()

    def untested(self) -> list[str]:
        return self.ledger.untested()

    def timeline(self) -> list[dict[str, Any]]:
        """Human-readable ordered list of tool calls in this investigation.

        Each entry shows *what* the agent examined, *when* in the clip, and
        *how confident* the evidence was — without exposing raw JSON payloads.
        Included in the report ``investigation`` block so the UI can render a
        plain-language trace rather than raw evidence IDs.
        """
        return [
            {
                "step": i + 1,
                "tool": record.tool,
                "window": list(record.window) if record.window else None,
                "summary": record.summary,
                "confidence": record.confidence,
                "seconds": record.seconds,
            }
            for i, record in enumerate(self.ledger.records())
        ]

    def skip_reasons(self) -> dict[str, str]:
        """For each untested dimension, a brief reason string.

        Currently always ``"not examined"`` (the agent chose not to call the
        tool). Future: distinguish ``"tool_error"`` once per-dimension error
        tracking is added to the ledger.
        """
        return {name: "not examined" for name in self.untested()}

    def snapshot(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "budget": self.budget.snapshot(),
            "coverage": self.coverage(),
            "untested": self.untested(),
            "skip_reasons": self.skip_reasons(),
            "timeline": self.timeline(),
            "evidence": len(self.ledger.records()),
        }


def new_run_id() -> str:
    """Filesystem-safe run id (no colons)."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:8]}"


__all__ = [
    "Budget",
    "BudgetExceeded",
    "Cancelled",
    "InvestigationContext",
    "InvestigationError",
    "ReportTarget",
    "new_run_id",
]
