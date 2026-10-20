from __future__ import annotations

from pathlib import Path

from coachme.benchmark.mapping import ensure_rater_mapping, preference_mode, stored
from coachme.benchmark.paths import atomic_write_json, read_json


def test_per_rater_mapping_is_persisted_and_deterministic(tmp_path: Path) -> None:
    atomic_write_json(
        tmp_path / "mapping.json",
        {"clips": {"clip-1": {"A": "standard", "B": "investigator"}}, "raters": {}},
    )
    first = ensure_rater_mapping(tmp_path, "run-1", "coach-a", "clip-1")
    second = ensure_rater_mapping(tmp_path, "run-1", "coach-a", "clip-1")
    assert first == second
    assert set(first.values()) == {"standard", "investigator"}
    saved = read_json(tmp_path / "mapping.json")
    assert stored(saved, "coach-a", "clip-1") == first


def test_preference_uses_the_rater_mapping() -> None:
    mapping = {"clips": {"clip-1": {"A": "standard", "B": "investigator"}}, "raters": {}}
    item = {"preferred": "A", "mapping": {"A": "investigator", "B": "standard"}}
    assert preference_mode(item, mapping, "coach-a", "clip-1") == "investigator"
