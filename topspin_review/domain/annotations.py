"""Shape annotations drawn on a frame (arrow / line / circle / pen). Pure."""

from __future__ import annotations

from typing import Any

TYPES = ("arrow", "line", "circle", "pen")
DEFAULT_COLOR = "#f97316"


def _c(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def normalize(items: Any) -> list[dict]:
    """Coerce a list of shapes into a clean, bounded form (normalized 0..1)."""
    out: list[dict] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type", ""))
        if kind not in TYPES:
            continue
        color = str(item.get("color") or DEFAULT_COLOR)[:16]
        if kind == "pen":
            pts = [
                [_c(p[0]), _c(p[1])]
                for p in (item.get("points") or [])
                if isinstance(p, (list, tuple)) and len(p) == 2
            ][:500]
            if len(pts) < 2:
                continue
            out.append({"type": "pen", "color": color, "points": pts})
        else:
            out.append(
                {
                    "type": kind,
                    "color": color,
                    "x1": _c(item.get("x1")),
                    "y1": _c(item.get("y1")),
                    "x2": _c(item.get("x2")),
                    "y2": _c(item.get("y2")),
                }
            )
    return out
