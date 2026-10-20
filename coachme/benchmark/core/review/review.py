"""Manual semantic review of Investigator evidence windows."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, atomic_write_text, read_json
from coachme.benchmark.core.data.schemas import clip_map, load_manifest, normalize_report
from coachme.benchmark.core.evaluation.matching import match_findings

HEADER = [
    "clip_id",
    "issue_index",
    "matched",
    "text",
    "times",
    "evidence_ids",
    "semantic_ok",
    "notes",
]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _review_rows(run_dir: Path) -> list[dict[str, Any]]:
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    manifest_path = Path(str(run.get("manifest_path") or ""))
    if not manifest_path.is_file():
        raise BenchmarkError("manifest not found")
    manifest, problems = load_manifest(manifest_path, require_files=False, verify_checksums=False)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    labels_path = Path(str(run.get("labels_path") or manifest_path.parent / "labels.json"))
    labels = read_json(labels_path, {})
    labels = labels if isinstance(labels, dict) else {}
    rows: list[dict[str, Any]] = []
    for clip_id, clip in clip_map(manifest).items():
        report = read_json(run_dir / "raw" / "investigator" / f"{clip_id}.json", None)
        if not isinstance(report, dict):
            continue
        issues = normalize_report(report, clip_id)
        trace = read_json(run_dir / "traces" / "investigator" / f"{clip_id}.json", {})
        evidence = trace.get("evidence") if isinstance(trace, dict) and isinstance(trace.get("evidence"), list) else []
        label_findings = ((labels.get("clips") or {}).get(clip_id) or {}).get("findings") or []
        match = match_findings(
            [item for item in label_findings if isinstance(item, dict)],
            issues,
            media_type=str(clip.get("media_type", "video")),
            evidence=evidence,
            require_evidence=True,
        )
        matched = {item["issue_index"] for item in match["matches"]}
        for index, issue in enumerate(issues):
            rows.append(
                {
                    "clip_id": clip_id,
                    "issue_index": index,
                    "matched": "yes" if index in matched else "no",
                    "text": issue.get("text", ""),
                    "times": ",".join(str(value) for value in issue.get("times") or []),
                    "evidence_ids": ";".join(issue.get("evidence_ids") or []),
                    "semantic_ok": "",
                    "notes": "",
                }
            )
    return rows


def write_template(run_dir: str | Path, out: str | Path) -> Path:
    """Write a blank review CSV for the run's Investigator findings."""
    rows = _review_rows(Path(run_dir).resolve())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    target = Path(out).expanduser()
    atomic_write_text(target, buffer.getvalue())
    return target


def _parse_bool(value: str) -> bool | None:
    text = (value or "").strip().lower()
    if not text:
        return None
    if text in {"yes", "y", "true", "1"}:
        return True
    if text in {"no", "n", "false", "0"}:
        return False
    raise BenchmarkError(f"semantic_ok must be yes/no (or blank), got {value!r}")


def import_review(
    run_dir: str | Path,
    csv_path: str | Path,
    *,
    reviewer: str,
) -> dict[str, Any]:
    """Import a reviewed CSV into ``evidence_review.json``."""
    run_dir = Path(run_dir).resolve()
    if not reviewer.strip():
        raise BenchmarkError("reviewer is required")
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    manifest_path = Path(str(run.get("manifest_path") or ""))
    manifest, _ = load_manifest(manifest_path, require_files=False, verify_checksums=False)
    clips = clip_map(manifest)
    raw = Path(csv_path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("review CSV must be UTF-8 or UTF-8-BOM") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != HEADER:
        raise BenchmarkError("review CSV header must be exactly: " + ",".join(HEADER))
    review = read_json(run_dir / "evidence_review.json", {})
    review = review if isinstance(review, dict) else {}
    clips_review = review.get("clips")
    clips_review = clips_review if isinstance(clips_review, dict) else {}
    seen: set[tuple[str, str]] = set()
    imported = 0
    problems: list[str] = []
    for line, row in enumerate(reader, start=2):
        clip_id = (row.get("clip_id") or "").strip()
        index = (row.get("issue_index") or "").strip()
        semantic = _parse_bool(row.get("semantic_ok", ""))
        if semantic is None:
            continue
        if clip_id not in clips:
            problems.append(f"line {line}: unknown clip {clip_id}")
            continue
        if not index.isdigit():
            problems.append(f"line {line}: issue_index must be an integer")
            continue
        if (clip_id, index) in seen:
            problems.append(f"line {line}: duplicate {clip_id} issue {index}")
            continue
        seen.add((clip_id, index))
        report = read_json(run_dir / "raw" / "investigator" / f"{clip_id}.json", {})
        issues = normalize_report(report, clip_id) if isinstance(report, dict) else []
        if int(index) >= len(issues):
            problems.append(f"line {line}: issue {index} out of range for {clip_id}")
            continue
        clip_review = clips_review.setdefault(clip_id, {})
        clip_review.setdefault("issues", {})[index] = {
            "semantic_ok": semantic,
            "notes": (row.get("notes") or "").strip(),
        }
        imported += 1
    if problems:
        raise BenchmarkError("invalid review CSV:\n- " + "\n- ".join(problems))
    if imported == 0:
        raise BenchmarkError("review CSV has no completed semantic_ok rows")
    review.update(
        {
            "version": 1,
            "run_id": run.get("run_id") or run_dir.name,
            "reviewer": reviewer.strip(),
            "updated_at": _now(),
            "clips": clips_review,
        }
    )
    atomic_write_json(run_dir / "evidence_review.json", review)
    return {"imported": imported, "reviewer": review["reviewer"]}


__all__ = ["HEADER", "import_review", "write_template"]
