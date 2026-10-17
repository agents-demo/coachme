"""Multi-session trend aggregation: recurring issues, metric trajectories, drill stats."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from fastapi import APIRouter

from topspin_review.integrations.storage import store

router = APIRouter()

# Metric keys we surface in the trend view (from report["metrics"]["mechanics"]).
_METRIC_KEYS = [
    ("lower_lateral_range", "Footwork range"),
    ("mean_energy", "Mean energy"),
    ("impact_count", "Impacts"),
]


@router.get("/trends")
def trends() -> dict:
    """Aggregate all saved reports into a trend summary.

    Returns:
      sessions: total session count
      top_issues: most-recurring issues sorted by frequency
      metrics: per-metric time series (only metrics present in ≥ 2 sessions)
      drill_rate: total drills across all sessions
    """
    reports = store.get_reports()
    n = len(reports)
    if n < 2:
        return {"sessions": n, "top_issues": [], "metrics": [], "drill_rate": {"total": 0}}

    # --- recurring issues ---
    all_issues: list[str] = []
    total_drills = 0
    for r in reports:
        for issue in r.get("issues") or []:
            if isinstance(issue, str):
                text = issue
            elif isinstance(issue, dict):
                text = issue.get("text") or issue.get("title") or ""
            else:
                text = str(issue)
            text = text.strip()[:100]
            if text:
                all_issues.append(text)
        total_drills += len(r.get("drills") or [])

    issue_counts = Counter(all_issues).most_common(10)
    top_issues = [
        {"text": text, "count": count, "pct": round(count / n * 100)}
        for text, count in issue_counts
        if count >= 2  # only show if it recurs across sessions
    ]

    # --- metric trajectories ---
    metrics: list[dict] = []
    for key, label in _METRIC_KEYS:
        points: list[dict] = []
        for r in reversed(reports):  # oldest first for the chart
            mech = (r.get("metrics") or {}).get("mechanics") or {}
            val = mech.get(key)
            if val is None:
                continue
            try:
                fval = round(float(val), 3)
            except (TypeError, ValueError):
                continue
            stem = Path(r.get("source", "")).stem or ""
            points.append({"stem": stem, "date": r.get("date", ""), "value": fval})
        if len(points) >= 2:
            metrics.append({"key": key, "label": label, "points": points})

    return {
        "sessions": n,
        "top_issues": top_issues,
        "metrics": metrics,
        "drill_rate": {"total": total_drills},
    }
