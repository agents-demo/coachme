from __future__ import annotations

import json
from pathlib import Path

from coachme.benchmark.core.data.paths import atomic_write_json, read_json
from coachme.benchmark.core.data.privacy import prune_expired, withdraw_clip
from tests.benchmark.conftest import labels_for, make_manifest


def _run(tmp_path: Path, manifest: Path) -> Path:
    atomic_write_json(tmp_path / "labels.json", labels_for(["clip-1"]))
    run = tmp_path / "runs" / "run-1"
    atomic_write_json(
        run / "run.json",
        {
            "run_id": "run-1",
            "status": "complete",
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "clips": {"clip-1": {"standard": {"status": "complete"}}},
            "clips_total": 1,
            "clips_complete": 1,
        },
    )
    atomic_write_json(run / "raw" / "standard" / "clip-1.json", {"issues": []})
    atomic_write_json(run / "ratings" / "coach-a.json", {"rater": "coach-a", "clips": {"clip-1": {}}})
    atomic_write_json(run / "score.json", {"run_id": "run-1"})
    atomic_write_json(
        run / "mapping.json",
        {"clips": {"clip-1": {"A": "standard", "B": "investigator"}}, "raters": {}},
    )
    return run


def test_withdraw_clip_removes_data_and_records_manifest(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    run = _run(tmp_path, manifest)
    clip_file = tmp_path / "clips" / "clip-1.mp4"
    assert clip_file.is_file()

    event = withdraw_clip(manifest, "clip-1", reason="consent withdrawn", data_root=tmp_path)
    assert event["clip_id"] == "clip-1"
    assert not clip_file.exists()
    assert read_json(manifest)["clips"] == []
    assert read_json(tmp_path / "labels.json")["clips"] == {}
    assert read_json(run / "run.json")["clips"] == {}
    assert not (run / "raw" / "standard" / "clip-1.json").exists()
    assert not (run / "score.json").exists()
    lines = (tmp_path / "deletion_manifest.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["reason"] == "consent withdrawn"


def test_prune_expired_clips(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    data = read_json(manifest)
    data["clips"][0]["consent"]["date"] = "2020-01-01"
    data["clips"][0]["consent"]["retention_days"] = 1
    atomic_write_json(manifest, data)
    _run(tmp_path, manifest)
    removed = prune_expired(manifest, data_root=tmp_path)
    assert len(removed) == 1
    assert read_json(manifest)["clips"] == []
