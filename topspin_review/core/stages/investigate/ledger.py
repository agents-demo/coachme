"""Run-scoped evidence ledger for investigator mode.

Each successful tool call becomes one immutable :class:`EvidenceRecord`. Large
payloads stay on disk; the model receives a compact envelope and can request
``details`` later with ``get_evidence``.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topspin_review.domain.evidence import EvidenceRecord, validate

_SUMMARY_LIMIT = 1000
_DETAILS_LIMIT = 2000


class EvidenceLedger:
    """Thread-safe, per-run collection of evidence records."""

    def __init__(self, root: str | Path, run_id: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self._lock = threading.Lock()
        self._records: list[EvidenceRecord] = []
        self._by_id: dict[str, EvidenceRecord] = {}

    def add(
        self,
        *,
        tool: str,
        args: dict[str, Any] | None,
        window: tuple[float, float] | None,
        result: Any,
        seconds: float,
        artifacts: list[str] | None = None,
        confidence: str | None = None,
    ) -> EvidenceRecord:
        """Persist a tool result and return its immutable evidence record."""
        payload = result if isinstance(result, dict) else {"summary": str(result)}
        times = _times(payload.get("times"))
        summary = _clip(str(payload.get("summary") or _compact(payload)), _SUMMARY_LIMIT)
        details = _clip(str(payload.get("details") or ""), _DETAILS_LIMIT)
        conf = str(confidence or payload.get("confidence") or "low").lower()
        if conf not in {"high", "medium", "low"}:
            conf = "low"

        with self._lock:
            number = len(self._records) + 1
            evidence_id = f"ev_{number:04d}"
            data_path = self.root / f"{evidence_id}.json"
            record = EvidenceRecord(
                id=evidence_id,
                run_id=self.run_id,
                tool=str(tool),
                args=dict(args or {}),
                window=window,
                times=times,
                summary=summary,
                details=details,
                confidence=conf,
                data_path=str(data_path),
                artifacts=list(artifacts if artifacts is not None else payload.get("artifacts") or []),
                seconds=round(float(seconds), 2),
                created_at=datetime.now(UTC).isoformat(),
            )
            problems = validate(record)
            if problems:
                raise ValueError(f"invalid evidence record: {', '.join(problems)}")

            persisted = dict(payload)
            persisted.pop("_frames", None)
            data_path.write_text(
                json.dumps(persisted, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
            self._records.append(record)
            self._by_id[record.id] = record
            return record

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        with self._lock:
            return self._by_id.get(str(evidence_id))

    def records(self) -> list[EvidenceRecord]:
        with self._lock:
            return list(self._records)

    def coverage(self) -> dict[str, bool]:
        used = {record.tool for record in self.records()}
        return {
            "motion": bool(used & {"get_overview", "measure_motion"}),
            "pose": "estimate_pose" in used,
            "vision": "look" in used,
            "ball": False,
        }

    def untested(self) -> list[str]:
        coverage = self.coverage()
        return [name for name, used in coverage.items() if not used]


def _times(value: Any) -> list[float]:
    if not isinstance(value, (list, tuple)):
        return []
    out: list[float] = []
    for item in value:
        try:
            out.append(round(float(item), 2))
        except (TypeError, ValueError):
            continue
    return out


def _compact(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


__all__ = ["EvidenceLedger"]
