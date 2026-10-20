from __future__ import annotations

import csv
from pathlib import Path

import pytest

from coachme.benchmark.paths import BenchmarkError, atomic_write_json, read_json
from coachme.benchmark.ratings import EXPORT_HEADER, RATER_HEADER, import_rating_csv, write_combined_sheet


def _run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    atomic_write_json(
        run_dir / "run.json",
        {"run_id": "run-1", "clips": {"clip-1": {}, "clip-2": {}}, "required_raters": 2},
    )
    return run_dir


def _csv(path: Path, *, header: list[str] | None = None, rows: list[dict] | None = None) -> Path:
    columns = header or RATER_HEADER
    rows = rows or [
        {
            "clip_id": "clip-1",
            "rater": "coach-a",
            "A_specific": 5,
            "A_supported": 5,
            "A_complete": 4,
            "A_honest": 5,
            "A_use": "yes",
            "B_specific": 4,
            "B_supported": 4,
            "B_complete": 4,
            "B_honest": 4,
            "B_use": "yes",
            "preferred": "A",
            "rationale": "A is more specific.",
            "notes": "",
        },
        {
            "clip_id": "clip-2",
            "rater": "coach-a",
            "A_specific": 4,
            "A_supported": 4,
            "A_complete": 4,
            "A_honest": 4,
            "A_use": "no",
            "B_specific": 4,
            "B_supported": 4,
            "B_complete": 4,
            "B_honest": 4,
            "B_use": "yes",
            "preferred": "B",
            "rationale": "B is more useful.",
            "notes": "",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\r\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_import_rating_csv_writes_sheet(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    path = _csv(tmp_path / "ratings.csv")
    sheet = import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=path)
    assert sheet["rater"] == "coach-a"
    assert len(sheet["clips"]) == 2
    assert all(item["submitted"] for item in sheet["clips"].values())
    assert read_json(run_dir / "ratings" / "coach-a.json")["clips"]["clip-1"]["preferred"] == "A"


def test_import_rejects_wrong_header_and_duplicate_without_force(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    wrong = _csv(tmp_path / "wrong.csv", header=RATER_HEADER[:-1])
    with pytest.raises(BenchmarkError, match="header"):
        import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=wrong)

    path = _csv(tmp_path / "ratings.csv")
    import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=path)
    with pytest.raises(BenchmarkError, match="already submitted"):
        import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=path)


def test_import_rejects_rationale_missing_for_preference(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    rows = [
        {
            "clip_id": "clip-1",
            "rater": "coach-a",
            "A_specific": 5,
            "A_supported": 5,
            "A_complete": 4,
            "A_honest": 5,
            "A_use": "yes",
            "B_specific": 4,
            "B_supported": 4,
            "B_complete": 4,
            "B_honest": 4,
            "B_use": "yes",
            "preferred": "A",
            "rationale": "",
            "notes": "",
        }
    ]
    path = _csv(tmp_path / "ratings.csv", rows=rows)
    with pytest.raises(BenchmarkError, match="rationale"):
        import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=path)


def test_combined_sheet_adds_adjudicated_preference(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    path = _csv(tmp_path / "ratings.csv")
    import_rating_csv(run_dir=run_dir, rater="coach-a", csv_path=path)
    atomic_write_json(
        run_dir / "adjudication.json",
        {"clips": {"clip-1": {"preferred": "B", "rationale": "adjudicated"}}},
    )
    target = write_combined_sheet(run_dir)
    assert target is not None
    with target.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == EXPORT_HEADER
        row = next(reader)
        assert row["adjudicated_preference"] == "B"
