"""Blind rating import, validation and combined export."""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, atomic_write_text, read_json
from coachme.benchmark.core.ratings.mapping import ensure_rater_mapping

RATER_HEADER = [
    "clip_id",
    "rater",
    "A_specific",
    "A_supported",
    "A_complete",
    "A_honest",
    "A_use",
    "B_specific",
    "B_supported",
    "B_complete",
    "B_honest",
    "B_use",
    "preferred",
    "rationale",
    "notes",
]
EXPORT_HEADER = RATER_HEADER[:13] + ["adjudicated_preference"] + RATER_HEADER[13:]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _rating_sheet(run_dir: Path, rater: str) -> dict[str, Any]:
    data = read_json(run_dir / "ratings" / f"{rater}.json", {})
    return data if isinstance(data, dict) else {}


def load_ratings(run_dir: Path) -> dict[str, dict[str, Any]]:
    ratings: dict[str, dict[str, Any]] = {}
    for path in sorted((run_dir / "ratings").glob("*.json")):
        data = read_json(path, {})
        if isinstance(data, dict) and data.get("rater"):
            ratings[str(data["rater"])] = data
    return ratings


def submitted_count(run_dir: Path, clip_ids: list[str]) -> int:
    count = 0
    for sheet in load_ratings(run_dir).values():
        clips = sheet.get("clips") or {}
        if clip_ids and all((clips.get(clip_id) or {}).get("submitted") for clip_id in clip_ids):
            count += 1
    return count


def _validate_row(row: dict[str, str], *, rater: str, clip_ids: set[str]) -> list[str]:
    problems: list[str] = []
    clip_id = (row.get("clip_id") or "").strip()
    if not clip_id:
        problems.append("clip_id is required")
    elif clip_id not in clip_ids:
        problems.append(f"unknown clip_id: {clip_id}")
    if (row.get("rater") or "").strip() != rater:
        problems.append("rater column does not match the selected rater")
    for prefix in ("A", "B"):
        for field in ("specific", "supported", "complete", "honest"):
            key = f"{prefix}_{field}"
            try:
                value = int(str(row.get(key, "")).strip())
            except ValueError:
                problems.append(f"{key} must be an integer 1-5")
            else:
                if not 1 <= value <= 5:
                    problems.append(f"{key} must be 1-5")
        use = (row.get(f"{prefix}_use") or "").strip().lower()
        if use not in {"yes", "no"}:
            problems.append(f"{prefix}_use must be yes or no")
    preferred = (row.get("preferred") or "").strip()
    if preferred not in {"A", "B", "tie"}:
        problems.append("preferred must be A, B or tie")
    if preferred in {"A", "B"} and not (row.get("rationale") or "").strip():
        problems.append("rationale is required when preferred is A or B")
    if (row.get("adjudicated_preference") or "").strip():
        problems.append("adjudicated_preference is export-only and not accepted on import")
    return problems


def import_rating_csv(
    *,
    run_dir: str | Path,
    rater: str,
    csv_path: str | Path,
    force: bool = False,
) -> dict[str, Any]:
    """Import one rater's CSV and write ``ratings/<rater>.json``."""
    run_dir = Path(run_dir).resolve()
    rater = rater.strip()
    if not rater:
        raise BenchmarkError("rater is required")
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    clip_ids = set((run.get("clips") or {}).keys())
    if not clip_ids:
        raise BenchmarkError("run has no clips")
    existing = _rating_sheet(run_dir, rater)
    if any((item or {}).get("submitted") for item in (existing.get("clips") or {}).values()) and not force:
        raise BenchmarkError(f"ratings for {rater} are already submitted; pass --force to replace")

    raw = Path(csv_path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BenchmarkError("CSV must be UTF-8 or UTF-8-BOM") from exc
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != RATER_HEADER:
        raise BenchmarkError("CSV header must be exactly: " + ",".join(RATER_HEADER))
    rows = list(reader)
    if not rows:
        raise BenchmarkError("CSV has no rows")

    problems: list[str] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, start=2):
        clip_id = (row.get("clip_id") or "").strip()
        if clip_id in seen:
            problems.append(f"row {index}: duplicate clip_id {clip_id}")
        seen.add(clip_id)
        for problem in _validate_row(row, rater=rater, clip_ids=clip_ids):
            problems.append(f"row {index}: {problem}")
    if problems:
        raise BenchmarkError("invalid rating CSV:\n- " + "\n- ".join(problems))

    clips: dict[str, Any] = {}
    for row in rows:
        clip_id = row["clip_id"].strip()
        clips[clip_id] = {
            "A_specific": int(row["A_specific"]),
            "A_supported": int(row["A_supported"]),
            "A_complete": int(row["A_complete"]),
            "A_honest": int(row["A_honest"]),
            "A_use": row["A_use"].strip().lower(),
            "B_specific": int(row["B_specific"]),
            "B_supported": int(row["B_supported"]),
            "B_complete": int(row["B_complete"]),
            "B_honest": int(row["B_honest"]),
            "B_use": row["B_use"].strip().lower(),
            "preferred": row["preferred"].strip(),
            "rationale": (row.get("rationale") or "").strip(),
            "notes": (row.get("notes") or "").strip(),
            "mapping": ensure_rater_mapping(run_dir, str(run.get("run_id") or run_dir.name), rater, clip_id),
            "submitted": True,
            "submitted_at": _now(),
        }
    sheet = {
        "version": 1,
        "run_id": run.get("run_id") or run_dir.name,
        "rater": rater,
        "updated_at": _now(),
        "clips": clips,
    }
    atomic_write_json(run_dir / "ratings" / f"{rater}.json", sheet)
    return sheet


def rater_packet_zip(run_dir: str | Path, raters: list[str]) -> bytes:
    """Build separate rater packets with A/B JSON and a blank CSV template."""
    run_dir = Path(run_dir).resolve()
    run = read_json(run_dir / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {run_dir}")
    mapping = read_json(run_dir / "mapping.json", {})
    mapped = (mapping.get("clips") or {}) if isinstance(mapping, dict) else {}
    clip_ids = list(mapped)
    if not clip_ids:
        blind = run_dir / "blind"
        clip_ids = sorted(path.name for path in blind.iterdir() if path.is_dir()) if blind.is_dir() else []
    if not clip_ids:
        raise BenchmarkError("run has no blind packets")
    clean_raters = []
    for rater in raters:
        name = str(rater).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]+", name or "") or name in {".", ".."}:
            raise BenchmarkError(f"invalid rater id: {rater}")
        clean_raters.append(name)
    if not clean_raters:
        raise BenchmarkError("at least one rater is required")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for rater in clean_raters:
            prefix = f"{rater}/"
            archive.writestr(
                prefix + "README.txt",
                "Rate each clip without seeing which mode produced A or B.\n"
                "Do not open mapping.json; this packet does not include it.\n"
                "Fill ratings.csv and import it with coachme-benchmark import.\n",
            )
            for clip_id in clip_ids:
                rater_mapping = ensure_rater_mapping(run_dir, str(run.get("run_id") or run_dir.name), rater, clip_id)
                canonical_map = mapped.get(clip_id) or {"A": "standard", "B": "investigator"}
                for label in ("A", "B"):
                    mode = rater_mapping[label]
                    source_label = "A" if canonical_map.get("A") == mode else "B"
                    path = run_dir / "blind" / clip_id / f"{source_label}.json"
                    if path.is_file():
                        data = read_json(path, {})
                        archive.writestr(
                            prefix + f"{clip_id}/{label}.json",
                            json.dumps(data, ensure_ascii=False, indent=2),
                        )
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=RATER_HEADER, lineterminator="\n")
            writer.writeheader()
            for clip_id in clip_ids:
                writer.writerow({"clip_id": clip_id, "rater": rater})
            archive.writestr(prefix + "ratings.csv", csv_buffer.getvalue())
    return buffer.getvalue()


def write_combined_sheet(run_dir: str | Path) -> Path | None:
    """Write ``rating_sheet.csv`` from all rater files and optional adjudication."""
    run_dir = Path(run_dir).resolve()
    ratings = load_ratings(run_dir)
    if not ratings:
        return None
    adjudication = read_json(run_dir / "adjudication.json", {})
    adjudicated = (adjudication.get("clips") or {}) if isinstance(adjudication, dict) else {}
    rows: list[dict[str, Any]] = []
    for rater, sheet in sorted(ratings.items()):
        for clip_id, item in sorted((sheet.get("clips") or {}).items()):
            row = {"clip_id": clip_id, "rater": rater}
            row.update({key: item.get(key, "") for key in RATER_HEADER[2:13]})
            decision = (adjudicated.get(clip_id) or {}).get("preferred", "")
            row["adjudicated_preference"] = decision
            row["rationale"] = item.get("rationale", "")
            row["notes"] = item.get("notes", "")
            rows.append(row)
    if not rows:
        return None
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    target = run_dir / "rating_sheet.csv"
    atomic_write_text(target, buffer.getvalue())
    return target


__all__ = [
    "EXPORT_HEADER",
    "RATER_HEADER",
    "import_rating_csv",
    "load_ratings",
    "rater_packet_zip",
    "submitted_count",
    "write_combined_sheet",
]
