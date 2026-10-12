"""CLI command: show recent reports."""

from __future__ import annotations

from topspin_review.domain import render
from topspin_review.integrations.storage import store
from topspin_review.surfaces.cli.commands._display import print_report


def run() -> int:
    reports = store.get_reports()
    if not reports:
        print("No reports yet. Run `analyze`.")
        return 0
    print(f"Saved reports ({len(reports)}):\n")
    for report in reports[-5:]:
        print(
            f"  {render.video_name(report)} · {report.get('date', '?')} · "
            f"{report.get('sport', '')} · {report.get('focus', '')}"
        )
    print()
    print_report(reports[-1])
    return 0
