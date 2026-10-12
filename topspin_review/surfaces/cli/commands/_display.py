"""Shared CLI output helpers (used by more than one command)."""

from __future__ import annotations

from topspin_review.domain import render


def print_list(label: str, items: list) -> None:
    if not items:
        return
    print(f"\n  {label}:")
    for item in items:
        text = render.issue_line(item) if label == "Issues" else str(item)
        print(f"    - {text}")


def print_report(report: dict) -> None:
    if not report:
        return
    print(f"\nReport — {render.video_name(report)} · {report.get('sport', '')} ({report.get('date', '')})")
    if report.get("summary"):
        print(f"\n  {report['summary']}")
    print_list("Strengths", report.get("strengths") or [])
    print_list("Issues", report.get("issues") or [])
    print_list("Drills", report.get("drills") or [])
    if report.get("focus"):
        print(f"\n  Focus next session: {report['focus']}")
    if report.get("progress"):
        print(f"\n  Progress vs last time: {report['progress']}")
    print_list("Limitations", report.get("limitations") or [])
