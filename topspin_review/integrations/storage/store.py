"""Local state: player profile and one report file per analyzed video.

Each analyzed video is saved as ``runtime/data/<video-stem>_report.json`` (for
example ``video11.mp4`` -> ``video11_report.json``), so a report is always
identified by the video file name it came from.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from topspin_review.integrations.storage import json_store, runtime

DATA_DIR = runtime.DATA_DIR
PROFILE_PATH = DATA_DIR / "profile.json"
REPORT_SUFFIX = "_report.json"

_current_video: str | None = None


def set_current_video(video_path: str | Path) -> str:
    """Remember which video the next saved report belongs to."""
    global _current_video
    _current_video = Path(video_path).stem
    return _current_video


def report_path(video_path: str | Path) -> Path:
    """Report file path for ``video_path``: ``<stem>_report.json``."""
    return DATA_DIR / f"{Path(video_path).stem}{REPORT_SUFFIX}"


def _current_report_path() -> Path | None:
    if not _current_video:
        return None
    return DATA_DIR / f"{_current_video}{REPORT_SUFFIX}"


def _read(path: Path, default: Any) -> Any:
    return json_store.read_json(path, default)


def _write(path: Path, data: Any) -> None:
    json_store.write_json(path, data)


def get_profile() -> dict[str, Any]:
    return _read(PROFILE_PATH, {})


def set_profile(profile: dict[str, Any]) -> dict[str, Any]:
    _write(PROFILE_PATH, profile)
    return profile


def get_reports() -> list[dict[str, Any]]:
    """All saved reports, oldest first (by file mtime) — one file per video."""
    paths = sorted(
        DATA_DIR.glob(f"*{REPORT_SUFFIX}"),
        key=lambda p: p.stat().st_mtime,
    )
    reports: list[dict[str, Any]] = []
    for path in paths:
        report = _read(path, {})
        if isinstance(report, dict) and report:
            reports.append(report)
    return reports


def latest_report() -> dict[str, Any] | None:
    """The most recently written report, or ``None``."""
    reports = get_reports()
    return reports[-1] if reports else None


def add_report(report: dict[str, Any]) -> dict[str, Any]:
    """Save the report for the current video to ``<stem>_report.json``."""
    path = _current_report_path()
    if path is None:
        raise RuntimeError("no current video set; call set_current_video() first")
    _write(path, report)
    return report


def recent_reports(n: int = 5) -> list[dict[str, Any]]:
    return get_reports()[-n:]


def find_report(video_or_stem: str) -> dict[str, Any] | None:
    """The stored report for a video path or stem, or ``None``.

    Accepts either a bare stem (which may itself contain dots, e.g. ``clip.v2``)
    or a full filename/path with an extension. The bare stem is tried first as a
    literal ``<stem>_report.json`` file, so dotted names aren't truncated by
    ``Path.stem``.
    """
    direct = DATA_DIR / f"{video_or_stem}{REPORT_SUFFIX}"
    if direct.exists():
        report = _read(direct, {})
        if isinstance(report, dict) and report:
            return report
    stem = Path(video_or_stem).stem
    matches = [r for r in get_reports() if Path(r.get("source", "")).stem == stem]
    return matches[-1] if matches else None


def patch_last_report(patch: dict[str, Any]) -> dict[str, Any] | None:
    """Merge ``patch`` into the current video's report file."""
    path = _current_report_path()
    if path is None or not path.exists():
        return None
    report = _read(path, {})
    if not isinstance(report, dict):
        return None
    report.update(patch)
    _write(path, report)
    return report


def set_annotations(stem: str, items: list[dict]) -> list[dict] | None:
    """Save shape annotations onto a stored report (found by video name or stem)."""
    report = find_report(stem)
    if not report:
        return None
    path = report_path(report.get("source") or stem)
    updated = dict(report)
    updated["annotations"] = items
    _write(path, updated)
    return items


def patch_report(stem: str, patch: dict) -> dict | None:
    """Merge display metadata (name, tags, notes) into a stored report.

    Only the keys present in ``patch`` are written; existing unrelated fields
    are preserved. Recognised keys: ``name`` (str), ``tags`` (list[str]),
    ``notes`` (str).
    """
    report = find_report(stem)
    if not report:
        return None
    path = report_path(report.get("source") or stem)
    updated = dict(report)
    for key in ("name", "tags", "notes"):
        if key in patch:
            updated[key] = patch[key]
    _write(path, updated)
    return updated


def append_feedback(stem: str, item: str, vote: str, note: str = "") -> list[dict] | None:
    """Append a thumbs-up/down vote to a stored report's feedback list.

    Each call adds one entry; votes are never overwritten so the full history
    is preserved for prompt improvement work.
    """
    import time

    report = find_report(stem)
    if not report:
        return None
    path = report_path(report.get("source") or stem)
    updated = dict(report)
    existing: list[dict] = list(updated.get("feedback") or [])
    existing.append({"item": item, "vote": vote, "note": note, "ts": int(time.time())})
    updated["feedback"] = existing
    _write(path, updated)
    return existing


def delete_report(video_or_stem: str) -> bool:
    """Delete one session's report and its generated artifacts/exports/cache."""
    stem = Path(video_or_stem).stem
    removed = False

    report = DATA_DIR / f"{stem}{REPORT_SUFFIX}"
    if report.exists():
        data = _read(report, {})
        report.unlink()
        removed = True
        source = data.get("source") if isinstance(data, dict) else None
        if source:
            media = Path(source)
            if media.parent == DATA_DIR and media.name.startswith("upload_") and media.exists():
                try:
                    media.unlink()
                except Exception:
                    pass

    for path in runtime.ARTIFACTS_DIR.glob(f"{stem}_*"):
        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink()
        except Exception:
            pass

    for path in (DATA_DIR / "exports").glob(f"{stem}_report.*"):
        try:
            path.unlink()
        except Exception:
            pass

    cache = runtime.CACHE_DIR / stem
    if cache.exists():
        shutil.rmtree(cache, ignore_errors=True)

    return removed


def reset() -> None:
    for path in DATA_DIR.glob(f"*{REPORT_SUFFIX}"):
        path.unlink()
