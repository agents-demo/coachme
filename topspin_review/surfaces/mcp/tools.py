"""The MCP tools exposed by the topspin-review server."""

from __future__ import annotations

from typing import Any


def register(server: Any) -> None:
    """Attach topspin-review's tools to a FastMCP ``server``."""

    @server.tool()
    def analyze_sport_video(video_path: str, region_box: list[float] | None = None) -> dict:
        """Analyze a racket-sport session video and return a coaching report.

        ``region_box`` optionally restricts analysis to [left, top, right, bottom] (0..1).
        """
        from topspin_review.core import service

        result = service.analyze_video_sync(video_path, region_box=service.parse_region_box(region_box))
        return {"report_path": result.get("report_path"), "report": result.get("report")}
