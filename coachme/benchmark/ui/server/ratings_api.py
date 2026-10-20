"""Blind rating and adjudication endpoints for the local review UI."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import atomic_write_json, read_json
from coachme.benchmark.core.ratings.mapping import canonical, ensure_rater_mapping, preference_mode
from coachme.benchmark.core.ratings.ratings import write_combined_sheet
from coachme.benchmark.ui.server import read

_SAFE = re.compile(r"^[A-Za-z0-9_-]+$")
SCORE_FIELDS = [
    "A_specific",
    "A_supported",
    "A_complete",
    "A_honest",
    "B_specific",
    "B_supported",
    "B_complete",
    "B_honest",
]
USE_FIELDS = ["A_use", "B_use"]


class RatingConflict(RuntimeError):
    pass


class RatingInvalid(RuntimeError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("invalid rating")
        self.problems = problems


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe(value: str, kind: str) -> str:
    if not _SAFE.fullmatch(value or "") or value in {".", ".."}:
        raise read.NotFound(f"unknown {kind}")
    return value


def _run_context(root: Path, run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_path = read.run_dir(root, run_id)
    detail = read.run_detail(root, run_id)
    mapping = read_json(run_path / "mapping.json", {})
    mapping = mapping if isinstance(mapping, dict) else {}
    return run_path, detail, mapping


def _sheet_path(run_path: Path, rater: str) -> Path:
    _safe(rater, "rater")
    return run_path / "ratings" / f"{rater}.json"


def _empty_sheet(run_id: str, rater: str) -> dict[str, Any]:
    return {"version": 1, "run_id": run_id, "rater": rater, "updated_at": "", "clips": {}}


def _sheet(run_path: Path, run_id: str, rater: str) -> dict[str, Any]:
    data = read_json(_sheet_path(run_path, rater), {})
    if not isinstance(data, dict) or not data:
        return _empty_sheet(run_id, rater)
    data.setdefault("clips", {})
    data["rater"] = rater
    data["run_id"] = data.get("run_id") or run_id
    return data


def _normalise_etag(value: str | None) -> str:
    return read.normalise_etag(value)


def _require_etag(current: str, if_match: str | None) -> None:
    supplied = _normalise_etag(if_match)
    if not supplied:
        raise RatingConflict("If-Match is required")
    if supplied != current:
        raise RatingConflict("rating sheet changed since load")


def _packet_clips(mapping: dict[str, Any], run_path: Path) -> list[str]:
    mapped = (mapping.get("clips") or {}).keys() if isinstance(mapping.get("clips"), dict) else []
    if mapped:
        return list(mapped)
    blind = run_path / "blind"
    if not blind.is_dir():
        return []
    return sorted(path.name for path in blind.iterdir() if path.is_dir())


def _blind_packet(run_path: Path, clip_id: str) -> dict[str, Any] | None:
    folder = run_path / "blind" / clip_id
    a = read_json(folder / "A.json", None)
    b = read_json(folder / "B.json", None)
    if not isinstance(a, dict) or not isinstance(b, dict):
        return None
    return {"A": a, "B": b}


def _validate_item(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise RatingInvalid(["rating must be an object"])
    problems: list[str] = []
    cleaned: dict[str, Any] = {}
    for field in SCORE_FIELDS:
        try:
            value = int(item.get(field))
        except (TypeError, ValueError):
            problems.append(f"{field} must be an integer 1-5")
            continue
        if not 1 <= value <= 5:
            problems.append(f"{field} must be 1-5")
        cleaned[field] = value
    for field in USE_FIELDS:
        value = str(item.get(field, "")).strip().lower()
        if value not in {"yes", "no"}:
            problems.append(f"{field} must be yes or no")
        cleaned[field] = value
    preferred = str(item.get("preferred", "")).strip()
    if preferred not in {"A", "B", "tie"}:
        problems.append("preferred must be A, B or tie")
    cleaned["preferred"] = preferred
    cleaned["rationale"] = str(item.get("rationale", "")).strip()
    cleaned["notes"] = str(item.get("notes", "")).strip()
    if preferred in {"A", "B"} and not cleaned["rationale"]:
        problems.append("rationale is required when preferred is A or B")
    if problems:
        raise RatingInvalid(problems)
    return cleaned


def rating_sheet(root: str | Path | None, run_id: str, rater: str) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, detail, mapping = _run_context(resolved, run_id)
    sheet = _sheet(run_path, run_id, rater)
    clips = _packet_clips(mapping, run_path)
    return {
        **sheet,
        "etag": read.etag_for(sheet),
        "required_clips": len(clips),
        "required_raters": detail.get("required_raters", 2),
    }


def rate_queue(root: str | Path | None, run_id: str, rater: str) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, detail, mapping = _run_context(resolved, run_id)
    sheet = _sheet(run_path, run_id, rater)
    clips = _packet_clips(mapping, run_path)
    items = []
    for clip_id in clips:
        item = (sheet.get("clips") or {}).get(clip_id)
        if item and item.get("submitted"):
            state = "submitted"
        elif item:
            state = "draft"
        else:
            state = "not_started"
        items.append(
            {
                "clip_id": clip_id,
                "has_packet": _blind_packet(run_path, clip_id) is not None,
                "state": state,
            }
        )
    submitted = sum(1 for item in items if item["state"] == "submitted")
    return {
        "run_id": run_id,
        "rater": rater,
        "etag": read.etag_for(sheet),
        "required_raters": detail.get("required_raters", 2),
        "clips": items,
        "submitted": submitted,
        "total": len(items),
        "all_submitted": bool(items) and submitted == len(items),
    }


def blind_packet(root: str | Path | None, run_id: str, clip_id: str, rater: str) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, _, _ = _run_context(resolved, run_id)
    clip_id = _safe(clip_id, "clip")
    sheet = _sheet(run_path, run_id, rater)
    item = (sheet.get("clips") or {}).get(clip_id) or {}
    if item.get("submitted"):
        raise RatingConflict("rating already submitted; reopen it to edit")
    packet = _blind_packet(run_path, clip_id)
    if packet is None:
        raise read.NotFound("blind packet not found")
    mapping_doc = read_json(run_path / "mapping.json", {})
    mapping_doc = mapping_doc if isinstance(mapping_doc, dict) else {}
    rater_map = ensure_rater_mapping(run_path, run_id, rater, clip_id)
    base = canonical(mapping_doc, clip_id)
    reports = {}
    for label in ("A", "B"):
        source_label = "A" if base.get("A") == rater_map[label] else "B"
        reports[label] = packet.get(source_label, {})
    return {
        "run_id": run_id,
        "clip_id": clip_id,
        "rater": rater,
        "etag": read.etag_for(sheet),
        "media_url": f"/api/runs/{run_id}/media/{clip_id}/source",
        "reports": reports,
        "rating": item or None,
        "mapping_visible": False,
        "mapping": None,
    }


def save_rating(
    root: str | Path | None,
    run_id: str,
    rater: str,
    clip_id: str,
    item: dict[str, Any],
    *,
    if_match: str | None,
) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, _, mapping = _run_context(resolved, run_id)
    clip_id = _safe(clip_id, "clip")
    if clip_id not in _packet_clips(mapping, run_path):
        raise read.NotFound("blind packet not found")
    sheet = _sheet(run_path, run_id, rater)
    _require_etag(read.etag_for(sheet), if_match)
    existing = (sheet.get("clips") or {}).get(clip_id) or {}
    if existing.get("submitted"):
        raise RatingConflict("rating already submitted; reopen it to edit")
    cleaned = _validate_item(item)
    cleaned["mapping"] = ensure_rater_mapping(run_path, run_id, rater, clip_id)
    cleaned.update({"submitted": False, "submitted_at": ""})
    sheet.setdefault("clips", {})[clip_id] = cleaned
    sheet["updated_at"] = _now()
    atomic_write_json(_sheet_path(run_path, rater), sheet)
    return {
        "run_id": run_id,
        "rater": rater,
        "clip_id": clip_id,
        "rating": cleaned,
        "etag": read.etag_for(sheet),
    }


def submit_ratings(root: str | Path | None, run_id: str, rater: str) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, _, mapping = _run_context(resolved, run_id)
    sheet = _sheet(run_path, run_id, rater)
    clips = _packet_clips(mapping, run_path)
    problems = []
    for clip_id in clips:
        item = (sheet.get("clips") or {}).get(clip_id)
        if not item:
            problems.append(f"{clip_id}: rating missing")
            continue
        try:
            _validate_item(item)
        except RatingInvalid as exc:
            problems.extend(f"{clip_id}: {problem}" for problem in exc.problems)
    if problems:
        raise RatingInvalid(problems)
    stamp = _now()
    for clip_id in clips:
        sheet["clips"][clip_id]["submitted"] = True
        sheet["clips"][clip_id]["submitted_at"] = stamp
    sheet["updated_at"] = stamp
    atomic_write_json(_sheet_path(run_path, rater), sheet)
    return {"rater": rater, "submitted": len(clips), "etag": read.etag_for(sheet)}


def reopen_rating(
    root: str | Path | None,
    run_id: str,
    rater: str,
    clip_id: str,
    *,
    reason: str,
) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, _, _ = _run_context(resolved, run_id)
    clip_id = _safe(clip_id, "clip")
    if not reason.strip():
        raise RatingInvalid(["reopen reason is required"])
    adjudication = read_json(run_path / "adjudication.json", {})
    if isinstance(adjudication, dict) and clip_id in (adjudication.get("clips") or {}):
        raise RatingConflict("cannot reopen after adjudication")
    sheet = _sheet(run_path, run_id, rater)
    item = (sheet.get("clips") or {}).get(clip_id)
    if not item:
        raise read.NotFound("rating not found")
    item["submitted"] = False
    item["submitted_at"] = ""
    sheet["updated_at"] = _now()
    atomic_write_json(_sheet_path(run_path, rater), sheet)
    event = {"at": sheet["updated_at"], "rater": rater, "clip_id": clip_id, "event": "reopen", "reason": reason}
    path = run_path / "rating_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return {"rater": rater, "clip_id": clip_id, "rating": item, "etag": read.etag_for(sheet)}


def _all_raters_submitted(run_path: Path, clip_id: str, required: int) -> bool:
    from coachme.benchmark.core.ratings.ratings import load_ratings

    count = 0
    for sheet in load_ratings(run_path).values():
        if ((sheet.get("clips") or {}).get(clip_id) or {}).get("submitted"):
            count += 1
    return count >= required


def adjudication_queue(root: str | Path | None, run_id: str) -> dict[str, Any]:
    from coachme.benchmark.core.ratings.ratings import load_ratings

    resolved = read.root_dir(root)
    run_path, detail, mapping = _run_context(resolved, run_id)
    clips = _packet_clips(mapping, run_path)
    ratings = load_ratings(run_path)
    decisions = read_json(run_path / "adjudication.json", {})
    decisions = (decisions.get("clips") or {}) if isinstance(decisions, dict) else {}
    required = int(detail.get("required_raters", 2))
    items = []
    for clip_id in clips:
        ready = _all_raters_submitted(run_path, clip_id, required)
        votes = []
        for rater, sheet in ratings.items():
            item = (sheet.get("clips") or {}).get(clip_id) or {}
            if item.get("submitted") and ready:
                votes.append({"rater": rater, "preferred": preference_mode(item, mapping, rater, clip_id)})
        items.append(
            {
                "clip_id": clip_id,
                "ready": ready,
                "votes": votes,
                "decision": decisions.get(clip_id),
            }
        )
    return {
        "run_id": run_id,
        "required_raters": required,
        "clips": items,
        "ready": all(item["ready"] for item in items) if items else False,
    }


def adjudication_detail(root: str | Path | None, run_id: str, clip_id: str) -> dict[str, Any]:
    from coachme.benchmark.core.ratings.ratings import load_ratings

    resolved = read.root_dir(root)
    run_path, detail, mapping = _run_context(resolved, run_id)
    clip_id = _safe(clip_id, "clip")
    required = int(detail.get("required_raters", 2))
    if not _all_raters_submitted(run_path, clip_id, required):
        raise RatingConflict("both raters must submit before adjudication")
    clip_map = (mapping.get("clips") or {}).get(clip_id) or {}
    if not clip_map:
        raise read.NotFound("mapping not found")
    reports = {}
    for mode in ("standard", "guided", "investigator"):
        report = read_json(run_path / "raw" / mode / f"{clip_id}.json", None)
        if isinstance(report, dict):
            reports[mode] = report
    ratings = {
        rater: ((sheet.get("clips") or {}).get(clip_id) or {}) for rater, sheet in load_ratings(run_path).items()
    }
    decisions = read_json(run_path / "adjudication.json", {})
    decisions = (decisions.get("clips") or {}) if isinstance(decisions, dict) else {}
    return {
        "run_id": run_id,
        "clip_id": clip_id,
        "media_url": f"/api/runs/{run_id}/media/{clip_id}/source",
        "mapping": clip_map,
        "reports": reports,
        "ratings": ratings,
        "decision": decisions.get(clip_id),
        "etag": read.etag_for(decisions),
    }


def save_adjudication(
    root: str | Path | None,
    run_id: str,
    clip_id: str,
    payload: dict[str, Any],
    *,
    if_match: str | None,
) -> dict[str, Any]:
    resolved = read.root_dir(root)
    run_path, detail, mapping = _run_context(resolved, run_id)
    clip_id = _safe(clip_id, "clip")
    required = int(detail.get("required_raters", 2))
    if not _all_raters_submitted(run_path, clip_id, required):
        raise RatingConflict("both raters must submit before adjudication")
    path = run_path / "adjudication.json"
    data = read_json(path, {"version": 1, "clips": {}})
    data = data if isinstance(data, dict) else {"version": 1, "clips": {}}
    data.setdefault("clips", {})
    _require_etag(read.etag_for(data.get("clips") or {}), if_match)
    preferred = str(payload.get("preferred", "")).strip()
    rationale = str(payload.get("rationale", "")).strip()
    if preferred not in {"A", "B", "tie"}:
        raise RatingInvalid(["preferred must be A, B or tie"])
    if not rationale:
        raise RatingInvalid(["rationale is required"])
    data["clips"][clip_id] = {"preferred": preferred, "rationale": rationale, "by": "local", "at": _now()}
    atomic_write_json(path, data)
    write_combined_sheet(run_path)
    return {
        "run_id": run_id,
        "clip_id": clip_id,
        "decision": data["clips"][clip_id],
        "mapping": (mapping.get("clips") or {}).get(clip_id, {}),
        "etag": read.etag_for(data.get("clips") or {}),
    }


def adjudication_etag(root: str | Path | None, run_id: str) -> str:
    resolved = read.root_dir(root)
    run_path = read.run_dir(resolved, run_id)
    data = read_json(run_path / "adjudication.json", {})
    clips = (data.get("clips") or {}) if isinstance(data, dict) else {}
    return read.etag_for(clips)


__all__ = [
    "RatingConflict",
    "RatingInvalid",
    "adjudication_detail",
    "adjudication_etag",
    "adjudication_queue",
    "blind_packet",
    "rate_queue",
    "rating_sheet",
    "reopen_rating",
    "save_adjudication",
    "save_rating",
    "submit_ratings",
]
