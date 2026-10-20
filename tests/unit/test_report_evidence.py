from __future__ import annotations

import json
from pathlib import Path

from coachme.core.stages.coach import report_tools
from coachme.domain import report as report_schema
from coachme.domain.evidence import EvidenceRecord


def _record(
    *,
    evidence_id: str = "ev_0001",
    tool: str = "look",
    window: tuple[float, float] | None = (2.0, 3.0),
) -> EvidenceRecord:
    return EvidenceRecord(
        id=evidence_id,
        run_id="20261018T090000Z-abc12345",
        tool=tool,
        window=window,
        times=[2.8],
        summary="contact near 2.8s",
        confidence="high",
    )


def _report(**patch):
    data = {
        "date": "2026-10-18",
        "sport": "table tennis",
        "summary": "Late contact.",
        "focus": "contact point",
        "limitations": ["Ball placement was not assessed."],
        "mode": "investigator",
        "evidence": ["ev_0001"],
        "investigation": {
            "coverage": {"motion": True, "pose": False, "vision": True, "ball": False},
            "untested": ["pose", "ball"],
            "stop_reason": "evidence_sufficient",
        },
        "issues": [
            {
                "issue": "Contact is late.",
                "evidence_times": [2.8],
                "evidence_ids": ["ev_0001"],
                "confidence": "high",
            }
        ],
    }
    data.update(patch)
    return data


def test_investigator_report_preserves_evidence_fields() -> None:
    normalized = report_schema.normalize(_report())
    assert normalized["mode"] == "investigator"
    assert normalized["evidence"] == ["ev_0001"]
    assert normalized["issues"][0]["evidence_ids"] == ["ev_0001"]


def test_investigator_report_accepts_cited_window() -> None:
    normalized = report_schema.normalize(_report())
    assert report_schema.validate(normalized, evidence_records=[_record()]) == []


def test_investigator_rejects_unknown_evidence() -> None:
    normalized = report_schema.normalize(_report())
    problems = report_schema.validate(normalized, evidence_records=[])
    assert any("unknown evidence_id" in item for item in problems)


def test_investigator_rejects_time_outside_cited_window() -> None:
    normalized = report_schema.normalize(
        _report(
            issues=[
                {
                    "issue": "Contact is late.",
                    "evidence_times": [5.0],
                    "evidence_ids": ["ev_0001"],
                    "confidence": "high",
                }
            ]
        )
    )
    problems = report_schema.validate(normalized, evidence_records=[_record()])
    assert any("outside cited windows" in item for item in problems)


def test_investigator_rejects_overview_only_evidence() -> None:
    normalized = report_schema.normalize(_report())
    problems = report_schema.validate(normalized, evidence_records=[_record(tool="get_overview")])
    assert any("only overview evidence" in item for item in problems)


def test_partial_investigator_report_can_have_no_issues_or_focus() -> None:
    normalized = report_schema.normalize(
        _report(
            focus="",
            issues=[],
            investigation={
                "coverage": {"motion": True, "pose": False, "vision": True, "ball": False},
                "untested": ["pose", "ball"],
                "stop_reason": "budget_exhausted",
            },
        )
    )
    assert report_schema.validate(
        normalized,
        evidence_records=[_record()],
        allow_partial=True,
    ) == []


def test_save_report_result_writes_only_valid_report(tmp_path: Path) -> None:
    target = tmp_path / "working_report.json"
    valid = report_tools.save_report_result(
        json.dumps(_report()),
        target=target,
        evidence_records=[_record()],
    )
    assert valid["ok"] is True
    assert json.loads(target.read_text(encoding="utf-8"))["mode"] == "investigator"

    bad_target = tmp_path / "bad.json"
    bad = report_tools.save_report_result(
        json.dumps(_report(issues=[])),
        target=bad_target,
        evidence_records=[_record()],
    )
    assert bad["ok"] is False
    assert bad["error"]["code"] == "INVALID_REPORT"
    assert not bad_target.exists()
