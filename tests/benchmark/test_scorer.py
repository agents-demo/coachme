from __future__ import annotations

import json
from pathlib import Path

from coachme.benchmark.core.data.paths import atomic_write_json
from coachme.benchmark.core.evaluation.scorer import score_run
from tests.benchmark.conftest import labels_for, make_manifest

SEQUENCES = [
    ["get_overview", "look", "estimate_pose"],
    ["get_overview", "estimate_pose", "look"],
    ["get_overview", "measure_motion", "look"],
]


def _report(*, investigator: bool) -> dict:
    report = {
        "date": "2026-10-20",
        "sport": "table tennis",
        "summary": "Late footwork at contact.",
        "strengths": [],
        "issues": [
            {
                "issue": "Late footwork at contact",
                "evidence_times": [2.0],
                "confidence": "medium",
            }
        ],
        "drills": [],
        "focus": "footwork",
        "progress": "",
        "limitations": [],
    }
    if investigator:
        report.update(
            {
                "mode": "investigator",
                "evidence": ["ev_look"],
                "investigation": {
                    "coverage": {"vision": True},
                    "untested": [],
                    "stop_reason": "evidence_sufficient",
                    "budget": {"tool_calls": 3, "frames": 12, "tokens": 150, "seconds": 15.0},
                },
            }
        )
        report["issues"][0]["evidence_ids"] = ["ev_look"]
    return report


def _rating_sheet(run_id: str, rater: str, clip_ids: list[str]) -> dict:
    return {
        "version": 1,
        "run_id": run_id,
        "rater": rater,
        "clips": {
            clip_id: {
                "A_specific": 5,
                "A_supported": 5,
                "A_complete": 5,
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
                "submitted": True,
            }
            for clip_id in clip_ids
        },
    }


def test_score_run_can_release_when_all_gates_pass(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=3)
    clip_ids = ["clip-1", "clip-2", "clip-3"]
    atomic_write_json(tmp_path / "labels.json", labels_for(clip_ids))
    run_dir = tmp_path / "run"
    atomic_write_json(
        run_dir / "run.json",
        {
            "run_id": "run-1",
            "status": "complete",
            "environment": "production",
            "modes": ["standard", "investigator"],
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "required_clips": 3,
            "required_raters": 2,
            "config_hash": "abc",
            "clips": {clip_id: {"standard": {}, "investigator": {}} for clip_id in clip_ids},
        },
    )
    for index, clip_id in enumerate(clip_ids):
        atomic_write_json(run_dir / "raw" / "standard" / f"{clip_id}.json", _report(investigator=False))
        atomic_write_json(run_dir / "raw" / "investigator" / f"{clip_id}.json", _report(investigator=True))
        atomic_write_json(
            run_dir / "traces" / "standard" / f"{clip_id}.json",
            {
                "mode": "standard",
                "clip_id": clip_id,
                "tool_sequence": [],
                "evidence": [],
                "budget": {"tool_calls": 0, "frames": 10, "tokens": 100, "seconds": 10.0},
                "status": "complete",
            },
        )
        atomic_write_json(
            run_dir / "traces" / "investigator" / f"{clip_id}.json",
            {
                "mode": "investigator",
                "clip_id": clip_id,
                "tool_sequence": SEQUENCES[index],
                "evidence": [{"id": "ev_look", "tool": "look", "window": [1.8, 2.2]}],
                "budget": {"tool_calls": 3, "frames": 12, "tokens": 150, "seconds": 15.0},
                "status": "complete",
            },
        )
    atomic_write_json(
        run_dir / "mapping.json",
        {
            "version": 1,
            "clips": {clip_id: {"A": "investigator", "B": "standard"} for clip_id in clip_ids},
        },
    )
    atomic_write_json(run_dir / "ratings" / "coach-a.json", _rating_sheet("run-1", "coach-a", clip_ids))
    atomic_write_json(run_dir / "ratings" / "coach-b.json", _rating_sheet("run-1", "coach-b", clip_ids))
    atomic_write_json(
        run_dir / "stability.json",
        {"stable": True, "within_48h": True, "same_config": True, "same_clips": True, "differences": {}},
    )
    atomic_write_json(
        run_dir / "tool_review.json",
        {
            "version": 1,
            "reviewer": "coach-a",
            "clips": {clip_id: {"issues": {"0": {"appropriate": True, "notes": ""}}} for clip_id in clip_ids},
        },
    )
    atomic_write_json(
        run_dir / "evidence_review.json",
        {
            "version": 1,
            "reviewer": "coach-a",
            "clips": {clip_id: {"issues": {"0": {"semantic_ok": True, "notes": ""}}} for clip_id in clip_ids},
        },
    )

    score = score_run(run_dir)
    assert score["investigator"]["precision"] == 1.0
    assert score["investigator"]["recall"] == 1.0
    assert score["investigator"]["path_diversity"] == 3
    assert score["coach"]["investigator"] == 3
    assert score["release_eligible"] is True, score["blocked_reasons"]
    assert score["gates"]["coach_preference"] is True
    assert (run_dir / "score.json").is_file()
    assert (run_dir / "report.md").is_file()
    assert (run_dir / "rating_sheet.csv").is_file()
    assert json.loads((run_dir / "score.json").read_text(encoding="utf-8"))["pass"] is True


def test_incomplete_pilot_is_blocked_and_reports_reasons(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    clip_ids = ["clip-1"]
    atomic_write_json(tmp_path / "labels.json", labels_for(clip_ids))
    run_dir = tmp_path / "run"
    atomic_write_json(
        run_dir / "run.json",
        {
            "run_id": "run-2",
            "status": "complete",
            "environment": "local",
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "required_clips": 8,
            "required_raters": 2,
            "clips": {"clip-1": {"standard": {}, "investigator": {}}},
        },
    )
    atomic_write_json(run_dir / "raw" / "standard" / "clip-1.json", _report(investigator=False))
    atomic_write_json(run_dir / "raw" / "investigator" / "clip-1.json", _report(investigator=True))
    atomic_write_json(
        run_dir / "traces" / "standard" / "clip-1.json",
        {"budget": {"tokens": 100, "seconds": 10.0}, "status": "complete"},
    )
    atomic_write_json(
        run_dir / "traces" / "investigator" / "clip-1.json",
        {
            "tool_sequence": ["get_overview", "look", "estimate_pose"],
            "evidence": [{"id": "ev_look", "tool": "look", "window": [1.8, 2.2]}],
            "budget": {"tokens": 150, "seconds": 15.0},
            "status": "complete",
        },
    )
    score = score_run(run_dir)
    assert score["release_eligible"] is False
    assert "clips_incomplete" in score["blocked_reasons"]
    assert "ratings_incomplete" in score["blocked_reasons"]
    assert "latency_environment_not_production" in score["blocked_reasons"]


def test_negative_control_is_never_release_eligible(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    clip_ids = ["clip-1"]
    atomic_write_json(tmp_path / "labels.json", labels_for(clip_ids))
    run_dir = tmp_path / "run"
    atomic_write_json(
        run_dir / "run.json",
        {
            "run_id": "negative",
            "label": "negative-control",
            "status": "complete",
            "environment": "production",
            "manifest_path": str(manifest),
            "labels_path": str(tmp_path / "labels.json"),
            "required_clips": 1,
            "required_raters": 0,
            "clips": {"clip-1": {"standard": {}, "investigator": {}}},
        },
    )
    atomic_write_json(run_dir / "raw" / "standard" / "clip-1.json", _report(investigator=False))
    atomic_write_json(run_dir / "raw" / "investigator" / "clip-1.json", _report(investigator=True))
    atomic_write_json(
        run_dir / "traces" / "standard" / "clip-1.json",
        {"budget": {"tokens": 100, "seconds": 10.0}, "status": "complete"},
    )
    atomic_write_json(
        run_dir / "traces" / "investigator" / "clip-1.json",
        {
            "tool_sequence": ["get_overview", "look", "estimate_pose"],
            "evidence": [{"id": "ev_look", "tool": "look", "window": [1.8, 2.2]}],
            "budget": {"tokens": 150, "seconds": 15.0},
            "status": "complete",
        },
    )
    score = score_run(run_dir)
    assert score["release_eligible"] is False
    assert "negative_control" in score["blocked_reasons"]
    assert score["negative_control"]["enabled"] is True
