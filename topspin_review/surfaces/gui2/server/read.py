"""Read model for reports (no Streamlit), shared by the API and the SPA."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topspin_review.domain import evaluate
from topspin_review.integrations.storage import json_store, runtime, store


def _when(stem: str) -> str:
    try:
        stamp = (runtime.DATA_DIR / f"{stem}_report.json").stat().st_mtime
        return datetime.fromtimestamp(stamp, tz=UTC).isoformat(timespec="seconds")
    except Exception:
        return ""


def _exists(path: Any) -> bool:
    return bool(path) and Path(str(path)).exists()


def _flag_probes(calls: list[dict]) -> list[dict]:
    """Mark openjiuwen's image-modality self-check ("What color is this image?") as a probe.

    It is a one-word capability check, not part of the analysis, so the UI can label it.
    """
    for call in calls:
        text = " ".join(str(m.get("content", "")) for m in (call.get("input") or []) if isinstance(m, dict))
        call["probe"] = "what color is this image" in text.lower()
    return calls


def _summary(report: dict) -> dict[str, Any]:
    """One dict per report for the history list."""
    source = report.get("source", "")
    score = evaluate.score(report)
    returns = (report.get("metrics") or {}).get("mechanics") or {}
    return {
        "stem": Path(source).stem or "report",
        "sport": report.get("sport", ""),
        "date": report.get("date", ""),
        "when": _when(Path(source).stem),
        "focus": report.get("focus", ""),
        "summary": report.get("summary", ""),
        "issue_count": len(report.get("issues") or []),
        "score": round(float(score.get("score", 0)), 1),
        "is_photo": Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"},
        "has_source": _exists(source),
        "has_frames": _exists((report.get("artifacts") or {}).get("frames")),
        "has_motion": _exists((report.get("artifacts") or {}).get("motion")),
        "has_pose": _exists((report.get("artifacts") or {}).get("pose")),
        "lower_range": returns.get("lower_lateral_range"),
    }


def list_reports() -> list[dict[str, Any]]:
    """All saved reports, newest first."""
    reports = store.get_reports()
    return [_summary(r) for r in reversed(reports)]


def get_report(stem: str) -> dict[str, Any] | None:
    """One full report plus its observability (usage, model calls, tool calls)."""
    report = store.find_report(stem)
    if not report:
        return None
    report = dict(report)
    report["stem"] = Path(report.get("source", "")).stem or stem
    artifacts = report.get("artifacts") or {}
    obs = json_store.read_json(artifacts.get("observability") or (runtime.ARTIFACTS_DIR / "x"), {})
    obs = obs if isinstance(obs, dict) else {}
    report["calls"] = _flag_probes(obs.get("calls") or [])
    report["tools"] = obs.get("tools") or []
    # The first timing entry is the pre-run "startup" overhead placeholder; older reports
    # labelled it "starting" — normalize for display.
    timeline = report.get("timings") or []
    report["timeline"] = [
        {**t, "stage": "startup" if t.get("stage") == "starting" else t.get("stage")} for t in timeline
    ]
    report["score"] = evaluate.score(report)
    report["has_source"] = _exists(report.get("source"))
    return report


def source_path(stem: str) -> Path | None:
    report = store.find_report(stem)
    if not report:
        return None
    path = Path(report.get("source", ""))
    return path if path.exists() else None


def artifact_path(stem: str, kind: str) -> Path | None:
    """Resolve a named artifact (frames/motion/pose/metrics/observability) for a report."""
    report = store.find_report(stem)
    if not report:
        return None
    path = (report.get("artifacts") or {}).get(kind)
    if path and Path(str(path)).exists():
        return Path(str(path))
    return None


def clip_path(stem: str, key: str) -> Path | None:
    """Resolve a highlight clip by its timestamp key for a report."""
    report = store.find_report(stem)
    if not report:
        return None
    path = (report.get("clips") or {}).get(str(key))
    if path and Path(str(path)).exists():
        return Path(str(path))
    return None
