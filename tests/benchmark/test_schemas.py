from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from coachme.benchmark.core.data.schemas import (
    labels_complete,
    load_manifest,
    normalize_report,
    validate_labels,
    validate_manifest,
)
from tests.benchmark.conftest import labels_for


def _manifest_data(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_valid_manifest_and_labels(manifest: Path) -> None:
    data = _manifest_data(manifest)
    assert validate_manifest(data, manifest_path=manifest) == []
    labels = labels_for(["clip-1"])
    assert validate_labels(labels, data, require_all_clips=True) == []
    assert labels_complete(data, labels)


def test_expired_consent_is_a_hard_error(manifest: Path) -> None:
    data = _manifest_data(manifest)
    data["clips"][0]["consent"]["expires"] = "2020-01-01"
    problems = validate_manifest(data, manifest_path=manifest, require_files=False)
    assert any("consent expired" in problem for problem in problems)


def test_clip_path_cannot_escape_fixture_root(manifest: Path) -> None:
    data = _manifest_data(manifest)
    data["clips"][0]["path"] = "../outside.mp4"
    problems = validate_manifest(data, manifest_path=manifest, require_files=False)
    assert any("must not contain '..'" in problem for problem in problems)


def test_checksum_mismatch_is_reported(manifest: Path) -> None:
    data = _manifest_data(manifest)
    data["clips"][0]["sha256"] = "0" * 64
    problems = validate_manifest(data, manifest_path=manifest, require_files=True)
    assert "clip clip-1: sha256 mismatch" in problems


def test_zero_findings_need_a_reason(manifest: Path) -> None:
    data = _manifest_data(manifest)
    labels = labels_for(["clip-1"])
    labels["clips"]["clip-1"]["findings"] = []
    problems = validate_labels(labels, data)
    assert any("zero findings require zero_finding_reason" in problem for problem in problems)


def test_ball_evidence_is_rejected(manifest: Path) -> None:
    data = _manifest_data(manifest)
    labels = labels_for(["clip-1"])
    labels["clips"]["clip-1"]["findings"][0]["required_evidence"] = ["ball"]
    problems = validate_labels(labels, data)
    assert any("ball is not available" in problem for problem in problems)


def test_missing_label_clip_is_incomplete(manifest: Path) -> None:
    data = _manifest_data(manifest)
    labels = deepcopy(labels_for(["clip-1"]))
    labels["clips"] = {}
    assert not labels_complete(data, labels)


def test_load_manifest_returns_problems(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{}", encoding="utf-8")
    _, problems = load_manifest(path)
    assert problems


def test_normalize_report_uses_theme_fallback_and_clamps_confidence() -> None:
    report = {
        "issues": [
            {"issue": "Backhand follow through drops late", "evidence_times": [2], "confidence": "certain"},
            {"issue": "Something unusual", "evidence_times": ["bad"], "evidence_ids": ["ev_1"]},
        ]
    }
    issues = normalize_report(report, "clip-1")
    assert issues[0]["themes"] == ["stroke"]
    assert issues[0]["confidence"] == "low"
    assert issues[1]["themes"] == ["other"]
    assert issues[1]["times"] == []
