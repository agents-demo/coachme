from __future__ import annotations

from pathlib import Path

from coachme.benchmark.negative_control import make_negative_control
from coachme.benchmark.paths import atomic_write_json, read_json
from coachme.benchmark.scorer import score_run
from tests.benchmark.conftest import labels_for, make_manifest


def test_negative_control_strips_findings_and_fails_gates(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    atomic_write_json(tmp_path / "labels.json", labels_for(["clip-1"]))
    source = tmp_path / "source"
    atomic_write_json(
        source / "run.json",
        {
            "run_id": "source",
            "status": "complete",
            "environment": "local",
            "modes": ["standard", "investigator"],
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "required_clips": 1,
            "required_raters": 0,
            "clips": {"clip-1": {"standard": {"status": "complete"}, "investigator": {"status": "complete"}}},
        },
    )
    report = {
        "summary": "A finding.",
        "issues": [
            {"issue": "Late footwork", "evidence_times": [2.0], "evidence_ids": ["ev_1"], "confidence": "medium"}
        ],
        "limitations": [],
    }
    atomic_write_json(source / "raw" / "standard" / "clip-1.json", report)
    atomic_write_json(source / "raw" / "investigator" / "clip-1.json", report)
    atomic_write_json(source / "traces" / "standard" / "clip-1.json", {"budget": {"tokens": 10, "seconds": 1}})
    atomic_write_json(
        source / "traces" / "investigator" / "clip-1.json",
        {
            "tool_sequence": ["get_overview", "look", "estimate_pose"],
            "evidence": [{"id": "ev_1", "tool": "look", "window": [1.8, 2.2]}],
            "budget": {"tokens": 20, "seconds": 2},
            "status": "complete",
        },
    )

    target = tmp_path / "negative"
    run = make_negative_control(source, target)
    assert run["label"] == "negative-control"
    assert read_json(target / "raw" / "investigator" / "clip-1.json")["issues"] == []
    score = score_run(target)
    assert score["negative_control"]["enabled"] is True
    assert len(score["negative_control"]["gates_failed"]) >= 3
    assert score["negative_control"]["sensitive"] is True
