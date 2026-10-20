"""Paths and constants for the gui2 server."""

from __future__ import annotations

from pathlib import Path

from coachme.integrations.storage import runtime

_HERE = Path(__file__).resolve().parent

CLIENT_BUILD = _HERE.parent / "client" / "build"  # the SvelteKit SPA (built static assets)
UPLOADS = runtime.DATA_DIR / "uploads"

ACCEPTED = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
