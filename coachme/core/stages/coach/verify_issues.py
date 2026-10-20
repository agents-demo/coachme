"""Verification pass: prune report issues the evidence does not support."""

from __future__ import annotations

from typing import Any

from coachme.core.stages import observe
from coachme.core.stages.coach.prompts import VERIFY_PROMPT, VERIFY_SYSTEM
from coachme.domain import report as report_schema
from coachme.integrations.agents import run_text


async def verify(report: dict, observations: str, measured_text: str, recorder: Any = None) -> dict:
    """Drop issues the model cannot ground in the evidence (best-effort)."""
    issues = list(report_schema.issues(report))
    if not issues:
        return report

    listed = "\n".join(
        f"[{i}] {item.get('issue', '')}" if isinstance(item, dict) else f"[{i}] {item}"
        for i, item in enumerate(issues)
    )
    evidence = f"{observations}\n{measured_text}"
    try:
        text = await run_text(VERIFY_SYSTEM, VERIFY_PROMPT.format(issues=listed, evidence=evidence), recorder=recorder)
        data = observe.extract_json(text)
        keep = data.get("supported")
    except Exception:
        return report

    if not isinstance(keep, list):
        return report

    kept = [issues[i] for i in keep if isinstance(i, int) and 0 <= i < len(issues)]
    if kept:
        report["issues"] = kept
        problems = data.get("unsupported_reasons")
        if isinstance(problems, dict) and problems:
            report.setdefault("limitations", [])
            report["limitations"].append("Some drafted issues were dropped as unsupported by the evidence.")
    return report
