"""Stroke / repetition segmentation (heuristic, pose-based).

A stroke is a peak in wrist speed. We track both wrists across the sampled
frames (mediapipe landmarks 15/16), take the faster wrist per step, and pick
local maxima above a relative threshold — merging ones closer than 0.4s. Each
stroke gets a dominant-hand guess. Heuristic: treat it as an indicator.
"""

from __future__ import annotations

import math

_MIN_GAP = 0.4
_REL_THRESHOLD = 0.35


def segment(pose_seq: list | None, timestamps: list[float]) -> list[dict]:
    """Return stroke events ``[{t, hand, strength}]`` from the pose wrists."""
    if not pose_seq:
        return []
    wrists: list[tuple[float, float, float, float] | None] = []
    for p in pose_seq:
        lm = (p or {}).get("landmarks")
        if lm and len(lm) > 16:
            wrists.append((lm[15][0], lm[15][1], lm[16][0], lm[16][1]))
        else:
            wrists.append(None)

    speed = [0.0] * len(wrists)
    hand: list[str | None] = [None] * len(wrists)
    for i in range(1, len(wrists)):
        a, b = wrists[i - 1], wrists[i]
        if not a or not b:
            continue
        ls = math.hypot(b[0] - a[0], b[1] - a[1])
        rs = math.hypot(b[2] - a[2], b[3] - a[3])
        speed[i] = max(ls, rs)
        hand[i] = "right" if rs >= ls else "left"
    peak = max(speed) if speed else 0.0
    if peak <= 0:
        return []
    threshold = peak * _REL_THRESHOLD

    events: list[dict] = []
    for i in range(1, len(speed) - 1):
        if speed[i] >= threshold and speed[i] >= speed[i - 1] and speed[i] >= speed[i + 1]:
            events.append(
                {"t": round(float(timestamps[i]), 2), "hand": hand[i] or "unknown", "strength": round(speed[i] / peak, 2)}
            )

    merged: list[dict] = []
    for e in events:
        if merged and e["t"] - merged[-1]["t"] < _MIN_GAP:
            if e["strength"] > merged[-1]["strength"]:
                merged[-1] = e
            continue
        merged.append(e)
    return merged
