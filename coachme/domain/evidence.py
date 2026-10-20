"""Evidence records for the investigator mode.

The domain layer owns the schema and validation; storage and file paths belong to
the implementation layer. Keeping this pure makes evidence rules reusable by the
report validator and the UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CONFIDENCE = {"high", "medium", "low"}


@dataclass(frozen=True)
class EvidenceRecord:
    """One immutable observation returned by an investigation tool."""

    id: str
    run_id: str
    tool: str
    tool_version: str = "1"
    args: dict[str, Any] = field(default_factory=dict)
    window: tuple[float, float] | None = None
    times: list[float] = field(default_factory=list)
    summary: str = ""
    details: str = ""
    confidence: str = "low"
    data_path: str = ""
    artifacts: list[str] = field(default_factory=list)
    seconds: float = 0.0
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["window"] = list(self.window) if self.window is not None else None
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceRecord:
        window = data.get("window")
        return cls(
            id=str(data.get("id", "")),
            run_id=str(data.get("run_id", "")),
            tool=str(data.get("tool", "")),
            tool_version=str(data.get("tool_version", "1")),
            args=dict(data.get("args") or {}),
            window=(float(window[0]), float(window[1])) if window else None,
            times=[round(float(t), 2) for t in (data.get("times") or [])],
            summary=str(data.get("summary", "")),
            details=str(data.get("details", "")),
            confidence=str(data.get("confidence", "low")),
            data_path=str(data.get("data_path", "")),
            artifacts=[str(path) for path in (data.get("artifacts") or [])],
            seconds=float(data.get("seconds", 0.0)),
            created_at=str(data.get("created_at", "")),
        )

    def envelope(self) -> dict[str, Any]:
        """Compact result returned to the model (never raw arrays)."""
        return {
            "ok": True,
            "evidence_id": self.id,
            "summary": self.summary,
            "details": self.details,
            "times": list(self.times),
            "confidence": self.confidence,
            "data_path": self.data_path,
            "artifacts": list(self.artifacts),
            "truncated": False,
        }


def validate(record: EvidenceRecord) -> list[str]:
    """Return schema problems; empty means the record is usable."""
    problems: list[str] = []
    if not record.id:
        problems.append("missing id")
    if not record.run_id:
        problems.append("missing run_id")
    if not record.tool:
        problems.append("missing tool")
    if record.confidence not in CONFIDENCE:
        problems.append(f"bad confidence: {record.confidence}")
    if record.window is not None:
        start, end = record.window
        if start < 0 or end <= start:
            problems.append(f"bad window: {record.window}")
    for value in record.times:
        if value < 0:
            problems.append(f"bad time: {value}")
            break
    return problems


def is_valid(record: EvidenceRecord) -> bool:
    return not validate(record)


__all__ = ["CONFIDENCE", "EvidenceRecord", "is_valid", "validate"]
