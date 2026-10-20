"""Request models for the gui2 server."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    video_path: str
    region_box: list[float] | None = None
    agentic: bool = False
    language: str = "en"
    mode: str | None = None
    """Explicit strategy name: ``deterministic``, ``agentic``, or ``investigator``.
    When set it takes precedence over the ``agentic`` flag."""
