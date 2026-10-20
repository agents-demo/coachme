from __future__ import annotations

from coachme.benchmark.matching import is_evidence_supported, match_findings


def label(text: str, times: list[float], *, themes: list[str] | None = None, required: list[str] | None = None) -> dict:
    return {
        "text": text,
        "themes": themes or ["footwork"],
        "evidence_times": times,
        "required_evidence": required or [],
    }


def issue(
    text: str, times: list[float], *, themes: list[str] | None = None, evidence_ids: list[str] | None = None
) -> dict:
    return {
        "text": text,
        "themes": themes or ["footwork"],
        "times": times,
        "evidence_ids": evidence_ids or [],
    }


def test_matching_is_one_to_one() -> None:
    labels = [label("late step", [2.0]), label("wide stance", [2.2])]
    issues = [issue("late step", [2.1]), issue("wide stance", [2.3])]
    result = match_findings(labels, issues)
    assert len(result["matches"]) == 2
    assert result["false_negatives"] == []
    assert result["false_positives"] == []


def test_time_tolerance_and_theme_are_required() -> None:
    labels = [label("late step", [2.0])]
    assert match_findings(labels, [issue("late step", [5.0])])["matches"] == []
    assert match_findings(labels, [issue("late step", [2.0], themes=["serve"])])["matches"] == []


def test_still_clips_match_on_theme_without_timestamps() -> None:
    labels = [label("late step", [])]
    result = match_findings(labels, [issue("late step", [])], media_type="still")
    assert len(result["matches"]) == 1


def test_investigator_evidence_must_cover_required_type() -> None:
    labels = [label("late step", [2.0], required=["pose"])]
    issues = [issue("late step", [2.0], evidence_ids=["ev_1"])]
    look = [{"id": "ev_1", "tool": "look", "window": [1.0, 3.0]}]
    pose = [{"id": "ev_1", "tool": "estimate_pose", "window": [1.0, 3.0]}]
    assert match_findings(labels, issues, evidence=look, require_evidence=True)["matches"] == []
    assert len(match_findings(labels, issues, evidence=pose, require_evidence=True)["matches"]) == 1


def test_overview_evidence_never_satisfies_support() -> None:
    issue_data = issue("late step", [2.0], evidence_ids=["ev_1"])
    records = {"ev_1": {"id": "ev_1", "tool": "get_overview", "window": [0.0, 10.0]}}
    assert not is_evidence_supported(issue_data, ["vision"], records)
