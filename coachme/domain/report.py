"""Report schema: normalize whatever the model returns into a stable shape.

Every claim should be backed by evidence, so an "issue" is a dict with the
timestamps that support it and a confidence. ``normalize`` tolerates the model
returning bare strings (older behaviour) and coerces everything to the schema.
"""

from __future__ import annotations

from typing import Any

from coachme.domain.evidence import EvidenceRecord

CONFIDENCE = {"high", "medium", "low"}


_CONF_ORDER = {"low": 0, "medium": 1, "high": 2}


def calibrate(report: dict, quality: dict | None) -> dict:
    """Cap issue confidence according to footage quality (measurement, not vibes)."""
    score = int((quality or {}).get("score", 100))
    cap = "low" if score < 40 else "medium" if score < 70 else "high"
    for issue in report.get("issues") or []:
        if isinstance(issue, dict):
            conf = issue.get("confidence", "low")
            if _CONF_ORDER.get(conf, 0) > _CONF_ORDER[cap]:
                issue["confidence"] = cap
    return report


def issues(report: dict) -> list[Any]:
    """Raw issue entries (dicts or legacy strings) from a report."""
    return list(report.get("issues") or [])


def issue_texts(report: dict) -> list[str]:
    """Issue texts only, tolerating both dict and legacy string issues."""
    out: list[str] = []
    for item in issues(report):
        out.append(str(item.get("issue", "")) if isinstance(item, dict) else str(item))
    return out


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value)]


def _as_issue(value: Any) -> dict | None:
    if isinstance(value, str):
        text = value.strip()
        return {"issue": text, "evidence_times": [], "confidence": "low"} if text else None
    if not isinstance(value, dict):
        return None
    times: list[float] = []
    for item in value.get("evidence_times") or []:
        try:
            times.append(round(float(item), 2))
        except (TypeError, ValueError):
            continue
    confidence = str(value.get("confidence", "low")).lower()
    if confidence not in CONFIDENCE:
        confidence = "low"
    evidence_ids = []
    for item in value.get("evidence_ids") or []:
        text = str(item).strip()
        if text:
            evidence_ids.append(text)
    return {
        "issue": str(value.get("issue", "")).strip(),
        "evidence_times": times,
        "evidence_ids": evidence_ids,
        "confidence": confidence,
    }


def normalize(raw: Any) -> dict:
    """Coerce a model report into the schema (unknown keys are dropped)."""
    raw = raw if isinstance(raw, dict) else {}
    issues = [issue for issue in (_as_issue(i) for i in (raw.get("issues") or [])) if issue]
    investigation = raw.get("investigation")
    return {
        "date": str(raw.get("date", "")),
        "sport": str(raw.get("sport", "")),
        "summary": str(raw.get("summary", "")),
        "strengths": _as_str_list(raw.get("strengths")),
        "issues": issues,
        "drills": _as_str_list(raw.get("drills")),
        "focus": str(raw.get("focus", "")),
        "progress": str(raw.get("progress", "")),
        "limitations": _as_str_list(raw.get("limitations")),
        "mode": str(raw.get("mode", "") or ""),
        "evidence": [str(item) for item in (raw.get("evidence") or []) if str(item).strip()],
        "investigation": dict(investigation) if isinstance(investigation, dict) else {},
    }


def validate(
    report: dict,
    *,
    evidence_records: list[EvidenceRecord] | None = None,
    allow_partial: bool = False,
) -> list[str]:
    """Return schema problems (empty means OK).

    ``evidence_records`` enables provenance/window checks for investigator
    reports. ``allow_partial`` relaxes only the fields that a budget-exhausted
    investigator report may legitimately omit.
    """
    problems: list[str] = []
    for field in ("date", "sport", "summary"):
        if not report.get(field):
            problems.append(f"missing {field}")
    if not allow_partial and not report.get("focus"):
        problems.append("missing focus")

    mode = str(report.get("mode") or "")
    if mode != "investigator":
        if not report.get("issues"):
            problems.append("no issues reported")
        for issue in report.get("issues") or []:
            if not issue.get("evidence_times"):
                problems.append(
                    f"issue without evidence_times: {issue.get('issue', '')[:40]}"
                )
            if issue.get("confidence") not in CONFIDENCE:
                problems.append(f"bad confidence: {issue.get('confidence')}")
        return problems

    investigation = report.get("investigation")
    if not isinstance(investigation, dict) or not investigation:
        problems.append("missing investigation")
        investigation = {}
    coverage = investigation.get("coverage")
    if not isinstance(coverage, dict):
        problems.append("missing investigation.coverage")
    untested = investigation.get("untested")
    if not isinstance(untested, list):
        problems.append("missing investigation.untested")
    if not investigation.get("stop_reason"):
        problems.append("missing investigation.stop_reason")
    if not report.get("evidence"):
        problems.append("missing evidence")
    if allow_partial and not report.get("limitations"):
        problems.append("partial report needs limitations")

    issues = report.get("issues") or []
    if not issues and not allow_partial:
        problems.append("no issues reported")

    records: dict[str, EvidenceRecord] = {}
    if evidence_records is not None:
        for record in evidence_records:
            if isinstance(record, EvidenceRecord):
                records[record.id] = record

    for issue in issues:
        if issue.get("confidence") not in CONFIDENCE:
            problems.append(f"bad confidence: {issue.get('confidence')}")
        if not issue.get("evidence_times"):
            problems.append(f"issue without evidence_times: {issue.get('issue', '')[:40]}")
        evidence_ids = issue.get("evidence_ids") or []
        if not evidence_ids:
            problems.append(f"issue without evidence_ids: {issue.get('issue', '')[:40]}")
            continue
        if evidence_records is None:
            continue
        cited: list[EvidenceRecord] = []
        for evidence_id in evidence_ids:
            record = records.get(str(evidence_id))
            if record is None:
                problems.append(f"unknown evidence_id: {evidence_id}")
                continue
            cited.append(record)
        non_overview = [record for record in cited if record.tool != "get_overview"]
        if not non_overview:
            problems.append(
                f"issue cites only overview evidence: {issue.get('issue', '')[:40]}"
            )
            continue
        windows = [record.window for record in non_overview if record.window is not None]
        if not windows:
            problems.append(
                f"issue evidence has no window: {issue.get('issue', '')[:40]}"
            )
            continue
        for value in issue.get("evidence_times") or []:
            if not any(
                start - 0.15 <= float(value) <= end + 0.15
                for start, end in windows
            ):
                problems.append(
                    f"evidence time {value} outside cited windows: "
                    f"{issue.get('issue', '')[:40]}"
                )
    return problems
