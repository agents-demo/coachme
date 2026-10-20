from __future__ import annotations

import csv
from pathlib import Path

from coachme.benchmark.core.data.paths import atomic_write_json, read_json
from coachme.benchmark.core.review.manual_review import (
    HALLUCINATION_HEADER,
    TOOL_HEADER,
    import_hallucination_review,
    import_tool_review,
    write_hallucination_template,
    write_tool_template,
)
from tests.benchmark.conftest import labels_for, make_manifest


def _run(tmp_path: Path, issue_text: str) -> Path:
    manifest = make_manifest(tmp_path, count=1)
    atomic_write_json(tmp_path / "labels.json", labels_for(["clip-1"]))
    run = tmp_path / "run"
    atomic_write_json(
        run / "run.json",
        {"run_id": "run-1", "manifest_path": str(manifest), "labels_path": str(tmp_path / "labels.json")},
    )
    report = {
        "issues": [
            {
                "issue": issue_text,
                "evidence_times": [2.0],
                "evidence_ids": ["ev_1"],
                "confidence": "medium",
            }
        ]
    }
    atomic_write_json(run / "raw" / "investigator" / "clip-1.json", report)
    atomic_write_json(run / "raw" / "standard" / "clip-1.json", report)
    atomic_write_json(
        run / "traces" / "investigator" / "clip-1.json",
        {"evidence": [{"id": "ev_1", "tool": "look", "window": [1.8, 2.2]}]},
    )
    return run


def _write_csv(path: Path, header: list[str], rows: list[dict]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_tool_review_round_trip(tmp_path: Path) -> None:
    run = _run(tmp_path, "Late footwork at contact")
    template = write_tool_template(run, tmp_path / "tool.csv")
    with template.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["tools"] == "look"
    rows[0]["appropriate"] = "yes"
    reviewed = _write_csv(tmp_path / "reviewed.csv", TOOL_HEADER, rows)
    assert import_tool_review(run, reviewed, reviewer="coach-a")["imported"] == 1
    assert read_json(run / "tool_review.json")["clips"]["clip-1"]["issues"]["0"]["appropriate"] is True


def test_hallucination_review_round_trip(tmp_path: Path) -> None:
    run = _run(tmp_path, "Ball speed was 42 km/h")
    template = write_hallucination_template(run, tmp_path / "hall.csv")
    with template.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["mode"] == "standard"
    rows[0]["confirmed"] = "no"
    reviewed = _write_csv(tmp_path / "reviewed.csv", HALLUCINATION_HEADER, rows)
    assert import_hallucination_review(run, reviewed, reviewer="coach-a")["imported"] == 1
    saved = read_json(run / "hallucination_review.json")
    assert saved["clips"]["clip-1"]["standard"]["issues"]["0"]["confirmed"] is False
