"""Optical flow motion (OpenCV) — a richer movement signal than frame-diff.

Dense Farneback flow between consecutive sampled frames; the per-step mean flow
magnitude captures direction-aware motion (a pan/step vs. a static frame), which
plain pixel difference conflates. Optional: returns ``[]`` without OpenCV.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

try:  # optional; degrades to an empty signal without it
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

_SIZE = (160, 90)


def available() -> bool:
    return cv2 is not None


def _gray(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("L").resize(_SIZE), dtype=np.uint8)


def magnitude(frames: list[Image.Image]) -> list[float]:
    """Mean optical-flow magnitude per consecutive frame pair."""
    if cv2 is None or len(frames) < 2:
        return []
    prev = _gray(frames[0])
    out: list[float] = []
    for frame in frames[1:]:
        cur = _gray(frame)
        flow = cv2.calcOpticalFlowFarneback(prev, cur, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        mag = float(np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2).mean())
        out.append(round(mag, 3))
        prev = cur
    return out
