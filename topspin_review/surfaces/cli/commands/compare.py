"""CLI command: compare two analyzed videos."""

from __future__ import annotations

from topspin_review.domain import compare as compare_mod
from topspin_review.integrations.storage import store


def run(video_a: str, video_b: str) -> int:
    older, newer = store.find_report(video_a), store.find_report(video_b)
    if not older or not newer:
        missing = video_a if not older else video_b
        print(f"No report for {missing}. Analyze it first.")
        return 1
    result = compare_mod.compare(older, newer)
    print(f"\n{result['text']}\n")
    if result["metric_deltas"]:
        print("Metric deltas (newer - older):")
        for key, value in result["metric_deltas"].items():
            print(f"  {key}: {value:+}")
    return 0
