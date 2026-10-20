"""Last-good report cache — a demo fallback when a live run fails.

After a successful analysis, the report is copied to ``runtime/data/demos/<stem>.json``.
If a later run for the same clip fails (model/network hiccup), the pipeline can fall
back to that recorded report and mark it ``fallback: true`` so the UI can label it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from coachme.integrations.storage import json_store, runtime


def _dir() -> Path:
    path = runtime.DATA_DIR / "demos"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save(stem: str, report: dict[str, Any]) -> None:
    if not stem or not report:
        return
    try:
        json_store.write_json(_dir() / f"{stem}.json", report)
    except Exception:
        pass


def load(stem: str) -> dict[str, Any] | None:
    if not stem:
        return None
    value = json_store.read_json(_dir() / f"{stem}.json", None)
    return value if isinstance(value, dict) and value else None
