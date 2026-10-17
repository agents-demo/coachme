"""Read model for reports (no Streamlit), shared by the API and the SPA."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from topspin_review.domain import drills as drills_catalog
from topspin_review.domain import game_reading
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
    returns = (report.get("metrics") or {}).get("mechanics") or {}
    metrics = report.get("metrics") or {}
    track = metrics.get("track") or []
    cxs = [float(t["cx"]) for t in track if isinstance(t, dict) and t.get("cx") is not None]
    subject_cx = round(sum(cxs) / len(cxs), 3) if cxs else 0.5
    # Prefer the pose body box: the motion-subject mask often covers most of the frame.
    pose_centers = []
    for frame in metrics.get("pose") or []:
        lm = (frame.get("lm") or frame.get("landmarks")) if isinstance(frame, dict) else None
        if not lm:
            continue
        xs = []
        for p in lm:
            if not isinstance(p, (list, tuple)) or len(p) < 3:
                continue
            vis = p[2] if len(p) == 3 else p[3]
            if (vis or 0) >= 0.5:
                xs.append(float(p[0]))
        if xs:
            pose_centers.append((min(xs) + max(xs)) / 2)
    if pose_centers:
        subject_cx = round(sum(pose_centers) / len(pose_centers), 3)
    return {
        "stem": Path(source).stem or "report",
        "sport": report.get("sport", ""),
        "date": report.get("date", ""),
        "when": _when(Path(source).stem),
        "name": report.get("name", ""),
        "tags": report.get("tags") or [],
        "notes": report.get("notes", ""),
        "focus": report.get("focus", ""),
        "summary": report.get("summary", ""),
        "issue_count": len(report.get("issues") or []),
        "drill_count": len(report.get("drills") or []),
        "is_photo": Path(source).suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"},
        "has_source": _exists(source),
        "has_frames": _exists((report.get("artifacts") or {}).get("frames")),
        "has_motion": _exists((report.get("artifacts") or {}).get("motion")),
        "has_pose": _exists((report.get("artifacts") or {}).get("pose")),
        "has_pose_hero": _exists((report.get("artifacts") or {}).get("pose_hero")),
        "lower_range": returns.get("lower_lateral_range"),
        "subject_cx": subject_cx,
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
    report["has_source"] = _exists(report.get("source"))
    report["drill_details"] = [drills_catalog.lookup(d) for d in (report.get("drills") or [])]
    report["tt_reading"] = game_reading.summarize(report.get("metrics") or {})
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
