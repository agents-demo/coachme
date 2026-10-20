"""Build a known-bad negative-control run from an existing standard run."""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.core.data.paths import BenchmarkError, atomic_write_json, read_json


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def make_negative_control(source_run: str | Path, out: str | Path) -> dict[str, Any]:
    """Copy Standard output and strip Investigator findings.

    The resulting run is deliberately bad. Scoring it must fail at least three
    release gates; the score records ``negative_control`` sensitivity.
    """
    source = Path(source_run).resolve()
    target = Path(out).resolve()
    run = read_json(source / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise BenchmarkError(f"run not found: {source}")
    clips = run.get("clips")
    if not isinstance(clips, dict) or not clips:
        raise BenchmarkError("source run has no clips")
    if target.exists() and any(target.iterdir()):
        raise BenchmarkError(f"output directory is not empty: {target}")
    target.mkdir(parents=True, exist_ok=True)

    new_run = copy.deepcopy(run)
    new_run.update(
        {
            "run_id": target.name,
            "label": "negative-control",
            "created_at": _now(),
            "updated_at": _now(),
            "status": "complete",
            "score_status": "missing",
            "release_eligible": False,
            "blocked_reasons": [],
        }
    )
    new_run.pop("score_updated_at", None)
    clips = new_run.get("clips") or {}
    for clip_id, state in clips.items():
        if not isinstance(state, dict):
            continue
        source_standard = source / "raw" / "standard" / f"{clip_id}.json"
        if source_standard.is_file():
            report = read_json(source_standard, {})
            if isinstance(report, dict) and report:
                atomic_write_json(target / "raw" / "standard" / f"{clip_id}.json", report)
        trace = read_json(source / "traces" / "standard" / f"{clip_id}.json", {})
        if isinstance(trace, dict) and trace:
            atomic_write_json(target / "traces" / "standard" / f"{clip_id}.json", trace)

        source_report = read_json(source / "raw" / "investigator" / f"{clip_id}.json", {})
        source_report = source_report if isinstance(source_report, dict) else {}
        bad_report = {
            "date": source_report.get("date", ""),
            "sport": source_report.get("sport", "table tennis"),
            "summary": "Negative control: no supported coaching findings were produced.",
            "strengths": [],
            "issues": [],
            "drills": [],
            "focus": "",
            "progress": "",
            "limitations": ["Deliberately degraded report for benchmark sensitivity."],
            "mode": "investigator",
            "evidence": [],
        }
        atomic_write_json(target / "raw" / "investigator" / f"{clip_id}.json", bad_report)
        source_trace = read_json(source / "traces" / "investigator" / f"{clip_id}.json", {})
        source_trace = source_trace if isinstance(source_trace, dict) else {}
        atomic_write_json(
            target / "traces" / "investigator" / f"{clip_id}.json",
            {
                "mode": "investigator",
                "clip_id": clip_id,
                "tool_sequence": [],
                "evidence": [],
                "budget": source_trace.get("budget") or {},
                "status": "complete",
            },
        )
        state.pop("investigator", None)
        state["investigator"] = {"status": "complete"}
    atomic_write_json(target / "run.json", new_run)
    return new_run


__all__ = ["make_negative_control"]
