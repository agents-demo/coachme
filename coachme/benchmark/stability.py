"""Reproducibility check across two benchmark runs."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.paths import BenchmarkError, atomic_write_json, read_json

MAX_DELTA = 0.05
MAX_HOURS = 48
METRICS = ("precision", "recall", "evidence_integrity")


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _delta(left: Any, right: Any) -> float | None:
    try:
        return round(abs(float(left) - float(right)), 4)
    except (TypeError, ValueError):
        return None


def compare_runs(run_a: str | Path, run_b: str | Path) -> dict[str, Any]:
    """Compare two score.json files and write ``stability.json`` to run A."""
    first = Path(run_a).resolve()
    second = Path(run_b).resolve()
    score_a = read_json(first / "score.json", {})
    score_b = read_json(second / "score.json", {})
    if not isinstance(score_a, dict) or not score_a:
        raise BenchmarkError(f"score.json missing in {first}")
    if not isinstance(score_b, dict) or not score_b:
        raise BenchmarkError(f"score.json missing in {second}")
    run_a_data = read_json(first / "run.json", {})
    run_b_data = read_json(second / "run.json", {})
    created_a = _timestamp((run_a_data or {}).get("created_at"))
    created_b = _timestamp((run_b_data or {}).get("created_at"))
    within_48h = bool(created_a and created_b and abs((created_a - created_b).total_seconds()) <= MAX_HOURS * 3600)
    config_a = (run_a_data or {}).get("config_hash")
    config_b = (run_b_data or {}).get("config_hash")
    same_config = bool(config_a and config_a == config_b)
    same_clips = score_a.get("clips") == score_b.get("clips")
    inv_a = score_a.get("investigator") or {}
    inv_b = score_b.get("investigator") or {}
    differences = {metric: _delta(inv_a.get(metric), inv_b.get(metric)) for metric in METRICS}
    within_tolerance = all(value is not None and value <= MAX_DELTA for value in differences.values())
    result = {
        "version": 1,
        "run_id": score_a.get("run_id") or first.name,
        "against": score_b.get("run_id") or second.name,
        "within_48h": within_48h,
        "same_config": same_config,
        "same_clips": same_clips,
        "differences": differences,
        "max_delta": MAX_DELTA,
        "within_tolerance": within_tolerance,
        "stable": within_48h and same_config and same_clips and within_tolerance,
        "checked_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    atomic_write_json(first / "stability.json", result)
    return result


__all__ = ["MAX_DELTA", "METRICS", "compare_runs"]
