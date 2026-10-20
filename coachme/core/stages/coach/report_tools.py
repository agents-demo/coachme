"""The agent's tools — thin wrappers over :mod:`coachme.integrations.storage.store`.

Plain callables; the backend agent builder decorates them (auto-extracting the
name, description and input schema from the function/docstring/signature).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from coachme.domain import report as report_schema
from coachme.integrations.storage import store


def _parse(raw: Any) -> Any:
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        return json.loads(text)
    raise ValueError(f"unsupported payload type: {type(raw)!r}")


def get_profile() -> str:
    """Return the player profile as JSON (sport, level, dominant_hand, goal)."""
    return json.dumps(store.get_profile(), ensure_ascii=False)


def recent_reports(n: int = 5) -> str:
    """Return the most recent saved coaching reports as a JSON array.

    Args:
        n: How many recent reports to return (default 5).
    """
    return json.dumps(store.recent_reports(int(n or 5)), ensure_ascii=False)


def save_report_result(
    report_json: str,
    *,
    target: str | Path | None = None,
    evidence_records: list | None = None,
    allow_partial: bool = False,
) -> dict[str, Any]:
    """Parse, validate and save a report; return a structured result.

    This is the single save path for both strategies. ``target`` is the
    investigator working report; when omitted, the deterministic current-video
    path is used.
    """
    try:
        raw = _parse(report_json)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": {
                "code": "INVALID_JSON",
                "message": f"could not parse report JSON: {exc}",
                "retryable": True,
            },
        }
    if not isinstance(raw, dict):
        return {
            "ok": False,
            "error": {
                "code": "INVALID_REPORT",
                "message": "report must be a JSON object",
                "retryable": True,
            },
        }
    raw.setdefault("date", date.today().isoformat())
    report = report_schema.normalize(raw)
    problems = report_schema.validate(
        report,
        evidence_records=evidence_records,
        allow_partial=allow_partial,
    )
    if problems and report.get("mode") == "investigator":
        return {
            "ok": False,
            "error": {
                "code": "INVALID_REPORT",
                "message": problems[0],
                "problems": problems,
                "retryable": True,
            },
        }
    if target is not None:
        store.add_report_at(target, report)
        path = str(target)
    else:
        store.add_report(report)
        path = ""
    return {"ok": True, "report_path": path, "report": report, "warnings": problems}


def save_report(report_json: str) -> str:
    """Save the coaching report.

    Args:
        report_json: JSON object string with keys date, sport, summary, strengths,
            issues (array of {issue, evidence_times, confidence}), drills, focus,
            progress, limitations.
    """
    result = save_report_result(report_json)
    if not result.get("ok"):
        return f"report rejected: {result.get('error', {}).get('message', 'invalid report')}"
    warnings = result.get("warnings") or []
    return "report saved" + (f" (warnings: {'; '.join(warnings)})" if warnings else "")


ALL_TOOLS = [get_profile, recent_reports, save_report]
