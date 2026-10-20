"""Read and write models for the local benchmark review UI.

The benchmark data root remains the source of truth. This module never writes
outside it and never exposes report data from label-only endpoints.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import atomic_write_json, data_root, read_json, sha256_json
from coachme.benchmark.core.data.schemas import (
    clip_map,
    clip_path,
    labels_complete,
    load_manifest,
    validate_labels,
)

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
MODES = ("standard", "guided", "investigator")


class NotFound(LookupError):
    pass


class Conflict(RuntimeError):
    pass


class Invalid(RuntimeError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("invalid label")
        self.problems = problems


def root_dir(root: str | Path | None = None) -> Path:
    return Path(root).expanduser().resolve() if root else data_root()


def _safe(value: str, *, kind: str) -> str:
    if not _SAFE_ID.fullmatch(value or "") or value in {".", ".."}:
        raise NotFound(f"unknown {kind}")
    return value


def run_dir(root: Path, run_id: str) -> Path:
    path = root / "runs" / _safe(run_id, kind="run")
    if not path.is_dir():
        raise NotFound("unknown run")
    return path


def _run(root: Path, run_id: str) -> dict[str, Any]:
    path = run_dir(root, run_id) / "run.json"
    data = read_json(path, {})
    if not isinstance(data, dict) or not data:
        raise NotFound("unknown run")
    return data


def _default_labels() -> dict[str, Any]:
    return {"version": 1, "labelers": [], "clips": {}}


def _normalise_labels(data: Any) -> dict[str, Any]:
    labels = dict(_default_labels())
    if isinstance(data, dict):
        labels.update(data)
    if not isinstance(labels.get("labelers"), list):
        labels["labelers"] = []
    if not isinstance(labels.get("clips"), dict):
        labels["clips"] = {}
    return labels


def _manifest(root: Path, run: dict[str, Any] | None = None) -> tuple[Path | None, dict[str, Any], list[str]]:
    candidates: list[Path] = []
    if run and run.get("manifest_path"):
        candidates.append(Path(str(run["manifest_path"])))
    candidates.append(root / "manifest.json")
    for candidate in candidates:
        if candidate.is_file():
            manifest, problems = load_manifest(candidate, require_files=False, verify_checksums=False)
            return candidate, manifest, problems
    return None, {}, ["manifest not found"]


def _labels_path(root: Path, run: dict[str, Any] | None, manifest_path: Path | None) -> Path:
    if run and run.get("labels_path"):
        return Path(str(run["labels_path"]))
    if manifest_path:
        return manifest_path.parent / "labels.json"
    return root / "labels.json"


def _labels(root: Path, run: dict[str, Any] | None = None) -> tuple[dict[str, Any], Path, Path | None, dict[str, Any]]:
    manifest_path, manifest, _ = _manifest(root, run)
    path = _labels_path(root, run, manifest_path)
    return _normalise_labels(read_json(path, {})), path, manifest_path, manifest


def etag_for(value: Any) -> str:
    return sha256_json(value)


def normalise_etag(value: str | None) -> str:
    text = (value or "").strip()
    if text.startswith("W/"):
        text = text[2:].strip()
    return text.strip('"')


def _score_status(run_path: Path, run: dict[str, Any], labels_path: Path) -> str:
    score_path = run_path / "score.json"
    if not score_path.is_file():
        return "missing"
    try:
        score_mtime = score_path.stat().st_mtime
    except OSError:
        return "missing"
    candidates = [run_path / "run.json", labels_path]
    candidates.extend((run_path / "ratings").glob("*.json"))
    candidates.extend((run_path / "raw").rglob("*.json"))
    candidates.extend((run_path / "traces").rglob("*.json"))
    for candidate in candidates:
        try:
            if candidate.is_file() and candidate.stat().st_mtime > score_mtime:
                return "stale"
        except OSError:
            continue
    return "current"


def _score(run_path: Path) -> dict[str, Any]:
    data = read_json(run_path / "score.json", {})
    return data if isinstance(data, dict) else {}


def _run_summary(root: Path, path: Path) -> dict[str, Any]:
    run = read_json(path / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise NotFound("unknown run")
    _, manifest, _ = _manifest(root, run)
    labels, labels_path, _, _ = _labels(root, run)
    score = _score(path)
    clips = clip_map(manifest) if manifest else {}
    score_status = _score_status(path, run, labels_path)
    gates = score.get("gates") or {}
    return {
        "run_id": run.get("run_id") or path.name,
        "label": run.get("label"),
        "created_at": run.get("created_at", ""),
        "environment": run.get("environment", "local"),
        "modes": run.get("modes") or [],
        "status": run.get("status", "unknown"),
        "clips_total": run.get("clips_total") or len(clips),
        "clips_complete": run.get("clips_complete", 0),
        "clips_failed": run.get("clips_failed", 0),
        "labels_complete": labels_complete(manifest, labels) if manifest else False,
        "set_complete": len(clips) >= int(run.get("required_clips") or 8),
        "score_status": score_status,
        "score_updated_at": score.get("score_updated_at"),
        "gates_pass": bool(gates) and all(value is True for value in gates.values()),
        "release_eligible": bool(score.get("release_eligible")) and score_status == "current",
        "blocked_reasons": score.get("blocked_reasons") or run.get("blocked_reasons") or [],
        "warning": None if manifest else "manifest not found",
    }


def list_runs(root: str | Path | None = None) -> list[dict[str, Any]]:
    resolved = root_dir(root)
    runs: list[dict[str, Any]] = []
    base = resolved / "runs"
    if not base.is_dir():
        return runs
    for path in sorted(base.iterdir()):
        if not path.is_dir() or not (path / "run.json").is_file():
            continue
        try:
            runs.append(_run_summary(resolved, path))
        except NotFound:
            continue
    return sorted(runs, key=lambda item: str(item.get("created_at", "")), reverse=True)


def run_detail(root: str | Path | None, run_id: str) -> dict[str, Any]:
    resolved = root_dir(root)
    path = run_dir(resolved, run_id)
    run = _run(resolved, run_id)
    summary = _run_summary(resolved, path)
    manifest_path, manifest, manifest_problems = _manifest(resolved, run)
    labels, labels_path, _, _ = _labels(resolved, run)
    score = _score(path)
    return {
        **summary,
        "run_id": run.get("run_id") or run_id,
        "label": run.get("label"),
        "status": run.get("status"),
        "environment": run.get("environment", "local"),
        "required_clips": run.get("required_clips", 8),
        "required_raters": run.get("required_raters", 2),
        "config_hash": run.get("config_hash"),
        "manifest_path": str(manifest_path) if manifest_path else "",
        "labels_path": str(labels_path),
        "manifest_problems": manifest_problems,
        "labels_complete": labels_complete(manifest, labels) if manifest else False,
        "score_available": (path / "score.json").is_file(),
        "score_status": summary["score_status"],
        "gates": score.get("gates") or {},
        "standard": score.get("standard") or {},
        "investigator": score.get("investigator") or {},
        "coach": score.get("coach") or {},
        "evidence_review": score.get("evidence_review") or {},
        "stability": score.get("stability") or {},
        "release_eligible": summary["release_eligible"],
        "blocked_reasons": summary["blocked_reasons"],
        "log_url": f"/api/runs/{run_id}/export/runner.log",
    }


def _label_status(label: Any, manifest: dict[str, Any], clip_id: str) -> str:
    if not isinstance(label, dict):
        return "missing"
    wrapper = {
        "version": 1,
        "labelers": [{"name": "ui"}],
        "clips": {clip_id: label},
    }
    return "complete" if not validate_labels(wrapper, manifest) else "draft"


def _report_status(run: dict[str, Any], clip_id: str, mode: str) -> dict[str, Any]:
    state = ((run.get("clips") or {}).get(clip_id) or {}).get(mode) or {}
    return {
        "status": state.get("status", "missing"),
        "issue_count": state.get("issue_count"),
        "seconds": state.get("seconds"),
        "error": state.get("error"),
    }


def _issue_count(run_path: Path, mode: str, clip_id: str) -> int | None:
    report = read_json(run_path / "raw" / mode / f"{clip_id}.json", None)
    if isinstance(report, dict):
        return len(report.get("issues") or [])
    return None


def clip_summaries(root: str | Path | None, run_id: str) -> list[dict[str, Any]]:
    resolved = root_dir(root)
    path = run_dir(resolved, run_id)
    run = _run(resolved, run_id)
    _, manifest, _ = _manifest(resolved, run)
    labels, _, _, _ = _labels(resolved, run)
    clips = clip_map(manifest)
    out: list[dict[str, Any]] = []
    for clip_id, clip in clips.items():
        reports = {}
        for mode in MODES:
            status = _report_status(run, clip_id, mode)
            status["issue_count"] = _issue_count(path, mode, clip_id)
            reports[mode] = status
        label = (labels.get("clips") or {}).get(clip_id)
        out.append(
            {
                "clip_id": clip_id,
                "media_type": clip.get("media_type", "video"),
                "duration_s": clip.get("duration_s", 0),
                "capture": clip.get("capture", ""),
                "sport": clip.get("sport", ""),
                "consent_ok": True,
                "reports": reports,
                "label_status": _label_status(label, manifest, clip_id),
            }
        )
    return out


def clip_detail(root: str | Path | None, run_id: str, clip_id: str) -> dict[str, Any]:
    resolved = root_dir(root)
    _safe(clip_id, kind="clip")
    path = run_dir(resolved, run_id)
    run = _run(resolved, run_id)
    manifest_path, manifest, manifest_problems = _manifest(resolved, run)
    clips = clip_map(manifest)
    clip = clips.get(clip_id)
    if not clip:
        raise NotFound("unknown clip")
    labels, _, _, _ = _labels(resolved, run)
    reports: dict[str, Any] = {}
    for mode in MODES:
        report = read_json(path / "raw" / mode / f"{clip_id}.json", None)
        if isinstance(report, dict):
            reports[mode] = report
    label = (labels.get("clips") or {}).get(clip_id)
    source: Path | None = None
    if manifest_path:
        try:
            candidate = clip_path(manifest, clip, manifest_path)
            source = candidate if candidate.is_file() else None
        except Exception:  # noqa: BLE001 - a missing manifest/clip is a normal UI state
            source = None
    artifacts: dict[str, str] = {}
    for _mode, report in reports.items():
        for kind, raw in (report.get("artifacts") or {}).items():
            if kind not in artifacts and raw and Path(str(raw)).is_file():
                artifacts[kind] = f"/api/runs/{run_id}/media/{clip_id}/artifact/{kind}"
    return {
        "run_id": run_id,
        "clip_id": clip_id,
        "clip": clip,
        "manifest_problems": manifest_problems,
        "reports": reports,
        "artifacts": artifacts,
        "traces": {
            mode: read_json(path / "traces" / mode / f"{clip_id}.json", {})
            for mode in MODES
            if (path / "traces" / mode / f"{clip_id}.json").is_file()
        },
        "label": label,
        "label_status": _label_status(label, manifest, clip_id),
        "has_source": source is not None,
        "media_url": f"/api/runs/{run_id}/media/{clip_id}/source",
    }


def label_context(root: str | Path | None, run_id: str, clip_id: str) -> dict[str, Any]:
    """Clip metadata + label for the label workspace; never report text."""
    resolved = root_dir(root)
    _safe(clip_id, kind="clip")
    run = _run(resolved, run_id)
    manifest_path, manifest, _ = _manifest(resolved, run)
    clip = clip_map(manifest).get(clip_id)
    if not clip:
        raise NotFound("unknown clip")
    labels, _, _, _ = _labels(resolved, run)
    label = (labels.get("clips") or {}).get(clip_id)
    source: Path | None = None
    if manifest_path:
        try:
            candidate = clip_path(manifest, clip, manifest_path)
            source = candidate if candidate.is_file() else None
        except Exception:  # noqa: BLE001
            source = None
    return {
        "run_id": run_id,
        "clip_id": clip_id,
        "clip": clip,
        "label": label,
        "label_status": _label_status(label, manifest, clip_id),
        "etag": etag_for(labels),
        "has_source": source is not None,
        "media_url": f"/api/runs/{run_id}/media/{clip_id}/source",
    }


def artifact_path(root: str | Path | None, run_id: str, clip_id: str, kind: str) -> Path:
    resolved = root_dir(root)
    _safe(clip_id, kind="clip")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", kind or ""):
        raise NotFound("unknown artifact")
    run_path = run_dir(resolved, run_id)
    for mode in MODES:
        report = read_json(run_path / "raw" / mode / f"{clip_id}.json", None)
        if not isinstance(report, dict):
            continue
        raw = (report.get("artifacts") or {}).get(kind)
        if not raw:
            continue
        path = Path(str(raw)).expanduser().resolve()
        try:
            path.relative_to(resolved)
        except ValueError as exc:
            raise NotFound("artifact outside data root") from exc
        if path.is_file():
            return path
    raise NotFound("artifact not found")


def source_path(root: str | Path | None, run_id: str, clip_id: str) -> Path:
    resolved = root_dir(root)
    _safe(clip_id, kind="clip")
    run = _run(resolved, run_id)
    manifest_path, manifest, _ = _manifest(resolved, run)
    clip = clip_map(manifest).get(clip_id)
    if not clip or not manifest_path:
        raise NotFound("unknown clip")
    try:
        path = clip_path(manifest, clip, manifest_path)
    except Exception as exc:  # noqa: BLE001
        raise NotFound("unknown clip") from exc
    if not path.is_file():
        raise NotFound("source not found")
    return path


def labels_document(root: str | Path | None = None) -> dict[str, Any]:
    resolved = root_dir(root)
    labels, path, _, _ = _labels(resolved)
    return {
        "version": labels.get("version", 1),
        "labelers": labels.get("labelers") or [],
        "clips": labels.get("clips") or {},
        "etag": etag_for(labels),
        "path": str(path),
    }


def get_label(root: str | Path | None, clip_id: str) -> dict[str, Any]:
    resolved = root_dir(root)
    labels, path, _, manifest = _labels(resolved)
    if manifest and clip_id not in clip_map(manifest):
        raise NotFound("unknown clip")
    return {
        "version": labels.get("version", 1),
        "clip_id": clip_id,
        "label": (labels.get("clips") or {}).get(clip_id),
        "etag": etag_for(labels),
        "path": str(path),
    }


def save_label(
    root: str | Path | None,
    clip_id: str,
    label: dict[str, Any],
    *,
    if_match: str | None,
    labeler: str = "coach-a",
) -> dict[str, Any]:
    resolved = root_dir(root)
    _safe(clip_id, kind="clip")
    labels, path, _, manifest = _labels(resolved)
    if manifest and clip_id not in clip_map(manifest):
        raise NotFound("unknown clip")
    current = etag_for(labels)
    supplied = normalise_etag(if_match)
    if not supplied:
        raise Conflict("If-Match is required")
    if supplied != current:
        raise Conflict("labels changed since load")
    if not isinstance(label, dict):
        raise Invalid(["label must be an object"])
    label = dict(label)
    label.pop("clip_id", None)
    labels["clips"][clip_id] = label
    name = (labeler or "coach-a").strip() or "coach-a"
    labelers = [item for item in labels.get("labelers") or [] if isinstance(item, dict)]
    if not any(str(item.get("name")) == name for item in labelers):
        labelers.append({"name": name, "labeled_at": date.today().isoformat()})
    labels["labelers"] = labelers
    probe = {"version": labels.get("version", 1), "labelers": labelers, "clips": {clip_id: label}}
    problems = validate_labels(probe, manifest)
    if problems:
        raise Invalid(problems)
    atomic_write_json(path, labels)
    return {
        "version": labels.get("version", 1),
        "clip_id": clip_id,
        "label": label,
        "etag": etag_for(labels),
        "path": str(path),
        "label_status": "complete",
    }


__all__ = [
    "Conflict",
    "Invalid",
    "NotFound",
    "artifact_path",
    "clip_detail",
    "clip_summaries",
    "etag_for",
    "get_label",
    "label_context",
    "labels_document",
    "list_runs",
    "normalise_etag",
    "root_dir",
    "run_detail",
    "run_dir",
    "save_label",
    "source_path",
]
