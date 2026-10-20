"""Clip-local one-to-one matching between coach labels and report findings."""

from __future__ import annotations

from functools import cache
from typing import Any

TOOL_EVIDENCE = {
    "estimate_pose": "pose",
    "look": "vision",
    "measure_motion": "motion",
}
TIME_TOLERANCE_S = 1.5


def _times(finding: dict[str, Any]) -> list[float]:
    out: list[float] = []
    for value in finding.get("times") or finding.get("evidence_times") or []:
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def _evidence_types(issue: dict[str, Any], evidence: dict[str, dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    for evidence_id in issue.get("evidence_ids") or []:
        record = evidence.get(str(evidence_id))
        if not record:
            continue
        kind = TOOL_EVIDENCE.get(str(record.get("tool", "")))
        if kind:
            found.add(kind)
    return found


def is_evidence_supported(
    issue: dict[str, Any],
    required: list[str] | None,
    evidence: dict[str, dict[str, Any]] | None,
) -> bool:
    """Check cited evidence records cover every required evidence type."""
    if not required:
        return True
    found = _evidence_types(issue, evidence or {})
    return set(required).issubset(found)


def _candidate_score(
    label: dict[str, Any],
    issue: dict[str, Any],
    *,
    media_type: str,
) -> float | None:
    if media_type == "still":
        return 0.0
    label_times = _times(label)
    issue_times = _times(issue)
    if not label_times or not issue_times:
        return None
    distance = min(abs(a - b) for a in label_times for b in issue_times)
    return distance if distance <= TIME_TOLERANCE_S else None


def match_findings(
    label_findings: list[dict[str, Any]],
    report_findings: list[dict[str, Any]],
    *,
    media_type: str = "video",
    evidence: list[dict[str, Any]] | None = None,
    require_evidence: bool = False,
) -> dict[str, Any]:
    """Return a deterministic maximum-cardinality, minimum-cost matching."""
    evidence_by_id = {
        str(record.get("id")): record for record in (evidence or []) if isinstance(record, dict) and record.get("id")
    }
    edges: list[list[tuple[int, float]]] = [[] for _ in label_findings]
    for label_index, label in enumerate(label_findings):
        required = label.get("required_evidence") if require_evidence else []
        for issue_index, issue in enumerate(report_findings):
            labels_themes = set(label.get("themes") or [])
            issue_themes = set(issue.get("themes") or [])
            if not labels_themes & issue_themes:
                continue
            distance = _candidate_score(label, issue, media_type=media_type)
            if distance is None:
                continue
            if require_evidence and not is_evidence_supported(issue, required, evidence_by_id):
                continue
            edges[label_index].append((issue_index, distance))

    report_text = [str(issue.get("text", "")).lower() for issue in report_findings]

    @cache
    def solve(label_index: int, used: int) -> tuple[int, float, tuple[str, ...], tuple[tuple[int, int], ...]]:
        if label_index >= len(label_findings):
            return 0, 0.0, (), ()
        best = solve(label_index + 1, used)
        for issue_index, distance in edges[label_index]:
            if used & (1 << issue_index):
                continue
            count, total_distance, texts, matches = solve(label_index + 1, used | (1 << issue_index))
            candidate = (
                count + 1,
                total_distance + distance,
                texts + (report_text[issue_index],),
                matches + ((label_index, issue_index),),
            )
            if candidate[0] > best[0]:
                best = candidate
            elif candidate[0] == best[0]:
                if (candidate[1], candidate[2]) < (best[1], best[2]):
                    best = candidate
        return best

    _, _, _, pairs = solve(0, 0)
    matched_labels = {label_index for label_index, _ in pairs}
    matched_issues = {issue_index for _, issue_index in pairs}
    return {
        "matches": [{"label_index": left, "issue_index": right} for left, right in pairs],
        "false_negatives": [index for index in range(len(label_findings)) if index not in matched_labels],
        "false_positives": [index for index in range(len(report_findings)) if index not in matched_issues],
    }


__all__ = ["TIME_TOLERANCE_S", "TOOL_EVIDENCE", "is_evidence_supported", "match_findings"]
