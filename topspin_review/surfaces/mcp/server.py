"""Stdio MCP server exposing ``analyze_sport_video`` to MCP clients.

Wrapping is MCP-native (FastMCP's ``@server.tool``); the tools live in
:mod:`topspin_review.surfaces.mcp.tools`.

    pip install -r requirements.txt
    python -m topspin_review.surfaces.mcp.server
"""

from __future__ import annotations

from topspin_review.core.bootstrap import setup


def main() -> None:
    setup()
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("MCP deps missing: pip install -r requirements.txt") from exc

    from topspin_review.surfaces.mcp import tools

    server = FastMCP("topspin-review")
    tools.register(server)
    server.run()


if __name__ == "__main__":
    main()
