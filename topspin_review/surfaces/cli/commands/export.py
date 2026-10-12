"""CLI command: export the latest (or a specific) report."""

from __future__ import annotations

from topspin_review.domain import render
from topspin_review.integrations import reporting
from topspin_review.integrations.storage import store


def run(video: str | None = None) -> int:
    report = store.find_report(video) if video else (store.get_reports() or [None])[-1]
    if not report:
        print(f"No report for {video}." if video else "No reports yet. Run `analyze` first.")
        return 1 if video else 0
    paths = reporting.write(report)
    print(f"Exported {render.video_name(report)}:")
    for kind, path in paths.items():
        print(f"  {kind}: {path}")
    return 0
