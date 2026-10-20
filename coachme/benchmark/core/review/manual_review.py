from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, atomic_write_text, read_json
from coachme.benchmark.core.data.schemas import clip_map, load_manifest, normalize_report
from coachme.benchmark.core.evaluation.matching import match_findings

TOOL_HEADER = ["clip_id", "issue_index", "text", "tools", "appropriate", "notes"]
HALLUCINATION_HEADER = ["mode", "clip_id", "issue_index", "text", "confirmed", "notes"]
FORBIDDEN = ("spin", "rpm", "km/h", "kph", "mph", "ball speed", "degrees", "exact angle")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _context(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    manifest_path = Path(str(run.get("manifest_path") or ""))
    if not manifest_path.is_file():
        raise BenchmarkError("manifest not found")
    manifest, problems = load_manifest(manifest_path, require_files=False, verify_checksums=False)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    labels = read_json(Path(str(run.get("labels_path") or manifest_path.parent / "labels.json")), {})
    return run, manifest, labels if isinstance(labels, dict) else {}


def _raw(run_dir: Path, mode: str, clip_id: str) -> dict[str, Any] | None:
    data = read_json(run_dir / "raw" / mode / f"{clip_id}.json", None)
    return data if isinstance(data, dict) else None


def _read_csv(path: str | Path, header: list[str]) -> list[dict[str, str]]:
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("review CSV must be UTF-8 or UTF-8-BOM") from exc
    reader = csv.DictReader(io.StringIO(text.replace("\r\n", "\n").replace("\r", "\n")))
    if reader.fieldnames != header:
        raise BenchmarkError("CSV header must be exactly: " + ",".join(header))
    return list(reader)


def _parse_bool(value: str, field: str) -> bool | None:
    text = (value or "").strip().lower()
    if not text:
        return None
    if text in {"yes", "y", "true", "1"}:
        return True
    if text in {"no", "n", "false", "0"}:
        return False
    raise BenchmarkError(f"{field} must be yes/no (or blank), got {value!r}")


def write_tool_template(run_dir: str | Path, out: str | Path) -> Path:
    run_path = Path(run_dir).resolve()
    _, manifest, labels = _context(run_path)
    rows: list[dict[str, Any]] = []
    for clip_id, clip in clip_map(manifest).items():
        report = _raw(run_path, "investigator", clip_id)
        if not report:
            continue
        issues = normalize_report(report, clip_id)
        trace = read_json(run_path / "traces" / "investigator" / f"{clip_id}.json", {})
        evidence = trace.get("evidence") if isinstance(trace, dict) else []
        findings = ((labels.get("clips") or {}).get(clip_id) or {}).get("findings") or []
        match = match_findings(
            [item for item in findings if isinstance(item, dict)],
            issues,
            media_type=str(clip.get("media_type", "video")),
            evidence=evidence,
            require_evidence=True,
        )
        matched = {item["issue_index"] for item in match["matches"]}
        by_id = {str(item.get("id")): item for item in evidence or [] if isinstance(item, dict) and item.get("id")}
        for index, issue in enumerate(issues):
            if index not in matched:
                continue
            tools = sorted(
                {str(by_id[item].get("tool", "")) for item in issue.get("evidence_ids") or [] if item in by_id}
            )
            rows.append(
                {
                    "clip_id": clip_id,
                    "issue_index": index,
                    "text": issue.get("text", ""),
                    "tools": ";".join(tools),
                    "appropriate": "",
                    "notes": "",
                }
            )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=TOOL_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    target = Path(out).expanduser()
    atomic_write_text(target, buffer.getvalue())
    return target


def import_tool_review(run_dir: str | Path, csv_path: str | Path, *, reviewer: str) -> dict[str, Any]:
    run_path = Path(run_dir).resolve()
    if not reviewer.strip():
        raise BenchmarkError("reviewer is required")
    _, manifest, _ = _context(run_path)
    known = clip_map(manifest)
    review = read_json(run_path / "tool_review.json", {})
    review = review if isinstance(review, dict) else {}
    clips = review.get("clips") if isinstance(review.get("clips"), dict) else {}
    imported = 0
    problems: list[str] = []
    seen: set[tuple[str, str]] = set()
    for line, row in enumerate(_read_csv(csv_path, TOOL_HEADER), start=2):
        clip_id = (row.get("clip_id") or "").strip()
        index = (row.get("issue_index") or "").strip()
        appropriate = _parse_bool(row.get("appropriate", ""), "appropriate")
        if appropriate is None:
            continue
        if clip_id not in known:
            problems.append(f"line {line}: unknown clip {clip_id}")
            continue
        if not index.isdigit():
            problems.append(f"line {line}: issue_index must be an integer")
            continue
        if (clip_id, index) in seen:
            problems.append(f"line {line}: duplicate {clip_id} issue {index}")
            continue
        seen.add((clip_id, index))
        report = _raw(run_path, "investigator", clip_id) or {}
        if int(index) >= len(normalize_report(report, clip_id)):
            problems.append(f"line {line}: issue {index} out of range")
            continue
        clips.setdefault(clip_id, {}).setdefault("issues", {})[index] = {
            "appropriate": appropriate,
            "notes": (row.get("notes") or "").strip(),
        }
        imported += 1
    if problems:
        raise BenchmarkError("invalid tool review CSV:\n- " + "\n- ".join(problems))
    if imported == 0:
        raise BenchmarkError("review CSV has no completed appropriate rows")
    review.update(
        {
            "version": 1,
            "reviewer": reviewer.strip(),
            "updated_at": _now(),
            "clips": clips,
        }
    )
    atomic_write_json(run_path / "tool_review.json", review)
    return {"imported": imported, "reviewer": review["reviewer"]}


def _flagged_issue_indices(report: dict[str, Any]) -> list[int]:
    issues = normalize_report(report, "")
    flagged = []
    for index, issue in enumerate(issues):
        text = str(issue.get("text", "")).lower()
        if any(word in text for word in FORBIDDEN):
            flagged.append(index)
    return flagged


def write_hallucination_template(run_dir: str | Path, out: str | Path) -> Path:
    run_path = Path(run_dir).resolve()
    _, manifest, _ = _context(run_path)
    rows: list[dict[str, Any]] = []
    for clip_id in clip_map(manifest):
        for mode in ("standard", "investigator"):
            report = _raw(run_path, mode, clip_id)
            if not report:
                continue
            issues = normalize_report(report, clip_id)
            for index in _flagged_issue_indices(report):
                rows.append(
                    {
                        "mode": mode,
                        "clip_id": clip_id,
                        "issue_index": index,
                        "text": issues[index].get("text", ""),
                        "confirmed": "",
                        "notes": "",
                    }
                )
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HALLUCINATION_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    target = Path(out).expanduser()
    atomic_write_text(target, buffer.getvalue())
    return target


def import_hallucination_review(run_dir: str | Path, csv_path: str | Path, *, reviewer: str) -> dict[str, Any]:
    run_path = Path(run_dir).resolve()
    if not reviewer.strip():
        raise BenchmarkError("reviewer is required")
    _, manifest, _ = _context(run_path)
    known = clip_map(manifest)
    review = read_json(run_path / "hallucination_review.json", {})
    review = review if isinstance(review, dict) else {}
    clips = review.get("clips") if isinstance(review.get("clips"), dict) else {}
    imported = 0
    problems: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for line, row in enumerate(_read_csv(csv_path, HALLUCINATION_HEADER), start=2):
        mode = (row.get("mode") or "").strip()
        clip_id = (row.get("clip_id") or "").strip()
        index = (row.get("issue_index") or "").strip()
        confirmed = _parse_bool(row.get("confirmed", ""), "confirmed")
        if confirmed is None:
            continue
        if mode not in {"standard", "investigator"}:
            problems.append(f"line {line}: mode must be standard or investigator")
            continue
        if clip_id not in known:
            problems.append(f"line {line}: unknown clip {clip_id}")
            continue
        if not index.isdigit():
            problems.append(f"line {line}: issue_index must be an integer")
            continue
        key = (mode, clip_id, index)
        if key in seen:
            problems.append(f"line {line}: duplicate {mode}/{clip_id}/{index}")
            continue
        seen.add(key)
        report = _raw(run_path, mode, clip_id) or {}
        if int(index) >= len(normalize_report(report, clip_id)):
            problems.append(f"line {line}: issue {index} out of range")
            continue
        clips.setdefault(clip_id, {}).setdefault(mode, {}).setdefault("issues", {})[index] = {
            "confirmed": confirmed,
            "notes": (row.get("notes") or "").strip(),
        }
        imported += 1
    if problems:
        raise BenchmarkError("invalid hallucination review CSV:\n- " + "\n- ".join(problems))
    if imported == 0:
        raise BenchmarkError("review CSV has no completed confirmed rows")
    review.update(
        {
            "version": 1,
            "reviewer": reviewer.strip(),
            "updated_at": _now(),
            "clips": clips,
        }
    )
    atomic_write_json(run_path / "hallucination_review.json", review)
    return {"imported": imported, "reviewer": review["reviewer"]}


__all__ = [
    "HALLUCINATION_HEADER",
    "TOOL_HEADER",
    "import_hallucination_review",
    "import_tool_review",
    "write_hallucination_template",
    "write_tool_template",
]
