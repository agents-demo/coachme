"""Manifest, label and report-normalisation contracts for the benchmark."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from coachme.benchmark.paths import (
    BenchmarkError,
    safe_relative,
    sha256_file,
)
from coachme.domain import progress

VERSION = 1
THEMES = {"footwork", "stroke", "preparation", "recovery", "serve", "other"}
SEVERITIES = {"low", "medium", "high"}
EVIDENCE_TYPES = {"motion", "pose", "ball", "vision"}
MODES = {"standard": "deterministic", "guided": "agentic", "investigator": "investigator"}
STRATEGY_NAMES = set(MODES.values())

_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _is_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and bool(_ID_RE.fullmatch(value))


def _date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _consent_records(clip: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if isinstance(clip.get("consent"), dict):
        records.append(clip["consent"])
    if isinstance(clip.get("consents"), list):
        records.extend(item for item in clip["consents"] if isinstance(item, dict))
    return records


def _fixture_root(manifest: dict[str, Any], manifest_path: str | Path | None) -> Path:
    raw = Path(str(manifest.get("fixture_root") or "clips")).expanduser()
    if raw.is_absolute():
        return raw.resolve()
    base = Path(manifest_path).expanduser().resolve().parent if manifest_path else Path.cwd()
    return (base / raw).resolve()


def clip_path(manifest: dict[str, Any], clip: dict[str, Any], manifest_path: str | Path | None = None) -> Path:
    """Resolve a clip path under the manifest's fixture root."""
    root = _fixture_root(manifest, manifest_path)
    raw = Path(str(clip.get("path") or ""))
    if raw.is_absolute():
        raise BenchmarkError(f"clip {clip.get('id', '?')}: path must be relative to fixture_root")
    resolved = (root / raw).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise BenchmarkError(f"clip {clip.get('id', '?')}: path escapes fixture_root") from exc
    return resolved


def validate_manifest(
    data: Any,
    *,
    manifest_path: str | Path | None = None,
    require_files: bool = True,
    verify_checksums: bool = True,
    today: date | None = None,
) -> list[str]:
    """Validate a manifest. Returns human-readable problems (empty means valid)."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["manifest must be a JSON object"]
    if data.get("version") != VERSION:
        problems.append(f"manifest.version must be {VERSION}")
    if not _is_str(data.get("fixture_root")):
        problems.append("manifest.fixture_root is required")
    clips = data.get("clips")
    if not isinstance(clips, list) or not clips:
        return problems + ["manifest.clips must be a non-empty list"]

    seen: set[str] = set()
    current = today or date.today()
    for index, clip in enumerate(clips):
        where = f"clips[{index}]"
        if not isinstance(clip, dict):
            problems.append(f"{where} must be an object")
            continue
        clip_id = clip.get("id")
        if not _safe_id(clip_id):
            problems.append(f"{where}.id must contain only letters, digits, '-' or '_'")
        elif clip_id in seen:
            problems.append(f"duplicate clip id: {clip_id}")
        else:
            seen.add(clip_id)
        where = f"clip {clip_id or index}"

        for field in ("path", "sport", "capture", "split", "source", "license", "sha256"):
            if not _is_str(clip.get(field)):
                problems.append(f"{where}: missing {field}")
        if clip.get("media_type") not in {"video", "still"}:
            problems.append(f"{where}: media_type must be 'video' or 'still'")
        if clip.get("split") not in {"benchmark", "holdout"}:
            problems.append(f"{where}: split must be 'benchmark' or 'holdout'")

        duration = clip.get("duration_s")
        if not isinstance(duration, (int, float)) or duration < 0:
            problems.append(f"{where}: duration_s must be >= 0")
        elif clip.get("media_type") == "video" and duration <= 0:
            problems.append(f"{where}: video duration_s must be > 0")
        elif clip.get("media_type") == "still" and duration != 0:
            problems.append(f"{where}: still duration_s must be 0")

        people = clip.get("people")
        if not isinstance(people, list) or not people or not all(_is_str(person) for person in people):
            problems.append(f"{where}: people must list at least one identifiable person")
            people = []
        consents = _consent_records(clip)
        if len(consents) < max(1, len(people)):
            problems.append(f"{where}: one consent record is required per person")
        for consent in consents:
            if consent.get("granted") is not True:
                problems.append(f"{where}: consent.granted must be true")
            for field in ("scope", "by"):
                if not _is_str(consent.get(field)):
                    problems.append(f"{where}: consent.{field} is required")
            granted = _date(consent.get("date"))
            expires = _date(consent.get("expires"))
            if granted is None:
                problems.append(f"{where}: consent.date must be YYYY-MM-DD")
            if expires is None:
                problems.append(f"{where}: consent.expires must be YYYY-MM-DD")
            elif expires < current:
                problems.append(f"{where}: consent expired on {expires.isoformat()}")
            retention = consent.get("retention_days")
            if retention is not None and (not isinstance(retention, int) or retention <= 0):
                problems.append(f"{where}: consent.retention_days must be a positive integer")

        if _is_str(clip.get("path")):
            try:
                safe_relative(clip["path"], label=f"{where}.path")
                if "fixture_root" in data and _is_str(data.get("fixture_root")):
                    path = clip_path(data, clip, manifest_path)
                    if require_files:
                        if not path.is_file():
                            problems.append(f"{where}: clip file not found: {path}")
                        elif verify_checksums and _is_str(clip.get("sha256")):
                            actual = sha256_file(path)
                            if actual.lower() != str(clip["sha256"]).lower():
                                problems.append(f"{where}: sha256 mismatch")
            except (BenchmarkError, OSError) as exc:
                problems.append(f"{where}: {exc}")
    return problems


def load_manifest(
    path: str | Path,
    *,
    require_files: bool = True,
    verify_checksums: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    from coachme.benchmark.paths import read_json

    data = read_json(path)
    if not isinstance(data, dict):
        return {}, [f"could not read manifest: {path}"]
    return data, validate_manifest(
        data,
        manifest_path=path,
        require_files=require_files,
        verify_checksums=verify_checksums,
    )


def clip_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(clip.get("id")): clip
        for clip in (manifest.get("clips") or [])
        if isinstance(clip, dict) and _is_str(clip.get("id"))
    }


def _validate_finding(
    finding: Any,
    *,
    where: str,
    duration: float,
    media_type: str,
) -> list[str]:
    problems: list[str] = []
    if not isinstance(finding, dict):
        return [f"{where} must be an object"]
    if not _safe_id(finding.get("id")):
        problems.append(f"{where}.id is required")
    text = finding.get("text")
    if not _is_str(text) or len(text) > 500:
        problems.append(f"{where}.text must be 1-500 characters")
    themes = finding.get("themes")
    if not isinstance(themes, list) or not themes:
        problems.append(f"{where}.themes must be a non-empty list")
    else:
        invalid = sorted({str(theme) for theme in themes} - THEMES)
        if invalid:
            problems.append(f"{where}.themes has invalid values: {', '.join(invalid)}")
    if finding.get("severity") not in SEVERITIES:
        problems.append(f"{where}.severity must be low, medium or high")
    required = finding.get("required_evidence")
    if not isinstance(required, list):
        problems.append(f"{where}.required_evidence must be a list")
    else:
        invalid = sorted({str(item) for item in required} - EVIDENCE_TYPES)
        if invalid:
            problems.append(f"{where}.required_evidence has invalid values: {', '.join(invalid)}")
        if "ball" in required:
            problems.append(f"{where}.required_evidence: ball is not available in the MVP")

    times = finding.get("evidence_times")
    if not isinstance(times, list):
        problems.append(f"{where}.evidence_times must be a list")
        times = []
    parsed: list[float] = []
    for value in times:
        try:
            number = float(value)
        except (TypeError, ValueError):
            problems.append(f"{where}.evidence_times contains a non-number")
            continue
        parsed.append(number)
        if number < 0:
            problems.append(f"{where}.evidence_times must be >= 0")
        elif media_type == "video" and number > duration + 0.01:
            problems.append(f"{where}.evidence_times exceeds clip duration")
        elif media_type == "still" and number != 0:
            problems.append(f"{where}.evidence_times for a still must be 0")
    if media_type == "video" and not parsed:
        problems.append(f"{where}.evidence_times requires at least one timestamp")
    return problems


def validate_labels(
    data: Any,
    manifest: dict[str, Any] | None = None,
    *,
    require_all_clips: bool = False,
) -> list[str]:
    """Validate coach ground truth, optionally against a manifest."""
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["labels must be a JSON object"]
    if data.get("version") != VERSION:
        problems.append(f"labels.version must be {VERSION}")
    labelers = data.get("labelers")
    if not isinstance(labelers, list) or not labelers:
        problems.append("labels.labelers must contain at least one labeler")
    elif not all(isinstance(item, dict) and _is_str(item.get("name")) for item in labelers):
        problems.append("each labeler needs a name")
    clips = data.get("clips")
    if not isinstance(clips, dict):
        return problems + ["labels.clips must be an object"]

    known = clip_map(manifest) if isinstance(manifest, dict) else {}
    if known:
        unknown = sorted(set(clips) - set(known))
        if unknown:
            problems.append("labels contain unknown clips: " + ", ".join(unknown))
        if require_all_clips:
            missing = sorted(set(known) - set(clips))
            if missing:
                problems.append("labels missing clips: " + ", ".join(missing))

    for clip_id, label in clips.items():
        where = f"clip {clip_id}"
        if not _safe_id(clip_id):
            problems.append(f"{where}: invalid clip id")
        if not isinstance(label, dict):
            problems.append(f"{where}: label must be an object")
            continue
        findings = label.get("findings")
        if not isinstance(findings, list):
            problems.append(f"{where}: findings must be a list")
            findings = []
        if len(findings) > 5:
            problems.append(f"{where}: at most five findings are allowed")
        zero_reason = label.get("zero_finding_reason")
        if not findings and not _is_str(zero_reason):
            problems.append(f"{where}: zero findings require zero_finding_reason")
        if label.get("acceptable_limitations") is not None and not isinstance(
            label.get("acceptable_limitations"), list
        ):
            problems.append(f"{where}: acceptable_limitations must be a list")

        clip = known.get(clip_id, {})
        duration = float(clip.get("duration_s", 0) or 0)
        media_type = str(clip.get("media_type", "video"))
        finding_ids: set[str] = set()
        for index, finding in enumerate(findings):
            finding_problems = _validate_finding(
                finding,
                where=f"{where}.findings[{index}]",
                duration=duration,
                media_type=media_type,
            )
            problems.extend(finding_problems)
            if isinstance(finding, dict) and _is_str(finding.get("id")):
                if finding["id"] in finding_ids:
                    problems.append(f"{where}: duplicate finding id {finding['id']}")
                finding_ids.add(finding["id"])
    return problems


def labels_complete(manifest: dict[str, Any], labels: Any) -> bool:
    if not isinstance(labels, dict):
        return False
    known = clip_map(manifest)
    if not known:
        return False
    if not set(known).issubset(set(labels.get("clips") or {})):
        return False
    return not validate_labels(labels, manifest, require_all_clips=True)


def normalize_report(report: Any, clip_id: str) -> list[dict[str, Any]]:
    """Normalize a raw report into the shared finding shape used by scoring."""
    report = report if isinstance(report, dict) else {}
    normalized: list[dict[str, Any]] = []
    for raw in report.get("issues") or []:
        if isinstance(raw, dict):
            text = str(raw.get("issue", "")).strip()
            themes = sorted(progress.classify(text)) or ["other"]
            times = _numbers(raw.get("evidence_times"))
            evidence_ids = [str(item) for item in (raw.get("evidence_ids") or []) if str(item).strip()]
            confidence = str(raw.get("confidence", "low")).lower()
        else:
            text = str(raw).strip()
            themes = sorted(progress.classify(text)) or ["other"]
            times = []
            evidence_ids = []
            confidence = "low"
        if not text:
            continue
        normalized.append(
            {
                "clip_id": clip_id,
                "text": text,
                "themes": themes,
                "times": times,
                "evidence_ids": evidence_ids,
                "confidence": confidence if confidence in SEVERITIES else "low",
            }
        )
    return normalized


def _numbers(values: Any) -> list[float]:
    out: list[float] = []
    for value in values or []:
        try:
            out.append(round(float(value), 2))
        except (TypeError, ValueError):
            continue
    return out


__all__ = [
    "EVIDENCE_TYPES",
    "MODES",
    "SEVERITIES",
    "STRATEGY_NAMES",
    "THEMES",
    "VERSION",
    "clip_map",
    "clip_path",
    "labels_complete",
    "load_manifest",
    "normalize_report",
    "validate_labels",
    "validate_manifest",
]
