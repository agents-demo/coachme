"""Request models for the gui2 server."""

from __future__ import annotations

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    video_path: str
    region_box: list[float] | None = None
    agentic: bool = False
    language: str = "en"
