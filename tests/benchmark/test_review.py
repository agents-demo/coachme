from __future__ import annotations

import csv
from pathlib import Path

import pytest

from coachme.benchmark.paths import BenchmarkError, atomic_write_json, read_json
from coachme.benchmark.review import HEADER, import_review, write_template
from tests.benchmark.conftest import labels_for, make_manifest


def _review_run(tmp_path: Path) -> Path:
    manifest = make_manifest(tmp_path, count=1)
    atomic_write_json(tmp_path / "labels.json", labels_for(["clip-1"]))
    run = tmp_path / "run"
    atomic_write_json(
        run / "run.json",
        {
            "run_id": "run-1",
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "status": "complete",
        },
    )
    atomic_write_json(
        run / "raw" / "investigator" / "clip-1.json",
        {
            "issues": [
                {
                    "issue": "Late footwork at contact",
                    "evidence_times": [2.0],
                    "evidence_ids": ["ev_1"],
                    "confidence": "medium",
                }
            ]
        },
    )
    atomic_write_json(
        run / "traces" / "investigator" / "clip-1.json",
        {"evidence": [{"id": "ev_1", "tool": "look", "window": [1.8, 2.2]}]},
    )
    return run


def test_review_template_and_import(tmp_path: Path) -> None:
    run = _review_run(tmp_path)
    target = write_template(run, tmp_path / "review.csv")
    with target.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["clip_id"] == "clip-1"
    assert rows[0]["matched"] == "yes"
    assert rows[0]["semantic_ok"] == ""
    rows[0]["semantic_ok"] = "yes"

    reviewed = tmp_path / "reviewed.csv"
    with reviewed.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    result = import_review(run, reviewed, reviewer="coach-a")
    assert result["imported"] == 1
    saved = read_json(run / "evidence_review.json")
    assert saved["clips"]["clip-1"]["issues"]["0"]["semantic_ok"] is True


def test_review_import_requires_completed_rows(tmp_path: Path) -> None:
    run = _review_run(tmp_path)
    target = write_template(run, tmp_path / "review.csv")
    with pytest.raises(BenchmarkError, match="no completed"):
        import_review(run, target, reviewer="coach-a")
