"""CLI command: clear saved reports."""

from __future__ import annotations

from topspin_review.integrations.storage import store


def run() -> int:
    store.reset()
    print("Cleared saved reports.")
    return 0
