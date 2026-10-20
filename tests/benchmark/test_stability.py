from __future__ import annotations

from pathlib import Path

from coachme.benchmark.core.data.paths import atomic_write_json, read_json
from coachme.benchmark.core.evaluation.stability import compare_runs


def _run(tmp_path: Path, name: str, *, precision: float, created: str) -> Path:
    path = tmp_path / name
    atomic_write_json(
        path / "run.json",
        {"run_id": name, "config_hash": "same", "created_at": created},
    )
    atomic_write_json(
        path / "score.json",
        {
            "run_id": name,
            "clips": 3,
            "investigator": {
                "precision": precision,
                "recall": 0.8,
                "evidence_integrity": 1.0,
            },
        },
    )
    return path


def test_stability_compares_metrics_and_window(tmp_path: Path) -> None:
    first = _run(tmp_path, "a", precision=0.8, created="2026-10-20T10:00:00Z")
    second = _run(tmp_path, "b", precision=0.83, created="2026-10-21T10:00:00Z")
    result = compare_runs(first, second)
    assert result["stable"] is True
    assert result["within_48h"] is True
    assert result["differences"]["precision"] == 0.03
    assert read_json(first / "stability.json")["stable"] is True


def test_stability_fails_when_variance_is_too_large(tmp_path: Path) -> None:
    first = _run(tmp_path, "a", precision=0.8, created="2026-10-20T10:00:00Z")
    second = _run(tmp_path, "b", precision=0.9, created="2026-10-20T10:00:00Z")
    result = compare_runs(first, second)
    assert result["stable"] is False
    assert result["within_tolerance"] is False
