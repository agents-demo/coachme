"""Ball detection, tracking and rally/contact segmentation (heuristic, no trained model).

The ball is found as a small, bright, roundish blob (warm/white colour prior) and
linked frame-to-frame with a constant-velocity tracker, with optional OpenCV
Hough-circle confirmation when ``cv2`` is installed. Direction changes along the
track are reported as candidate contacts/bounces, and apparent blob size gives a
crude monocular **depth** proxy so a shallow 3D trajectory can be plotted.

Everything here is heuristic and low confidence — it is a signal for the report
and the UI, not a measurement.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from topspin_review.core import config
from topspin_review.core.video import cvutil
from topspin_review.integrations import ballmodel

try:  # optional accelerator; the module degrades gracefully without it
    import cv2
except ImportError:  # pragma: no cover - depends on the environment
    cv2 = None

_SIZE = (160, 90)
_MIN_AREA = 2
_MAX_AREA = 200
_MAX_STEP = 0.16  # normalized per-frame link distance
_MAX_MISSED = 2
_MIN_TRAVEL = 0.05  # a real ball crosses the frame; reject near-static false positives
_REF_RADIUS = 5.0  # px at analysis size ~ "ball at nominal distance" (for depth)


def _rgb(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB").resize(_SIZE), dtype=np.float32) / 255.0


def _color_mask(img: Image.Image) -> np.ndarray:
    hsv = cvutil.rgb_to_hsv(_rgb(img))
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    warm = (h > 0.02) & (h < 0.17) & (s > 0.35) & (v > 0.65)
    white = (s < 0.25) & (v > 0.85)
    return (warm | white) & (v > 0.6)


def _circles(img: Image.Image) -> list[tuple[float, float, float]]:
    """Hough circles (normalized cx, cy, r) when OpenCV is available."""
    if cv2 is None:
        return []
    gray = np.asarray(img.convert("L").resize(_SIZE), dtype=np.uint8)
    gray = cv2.medianBlur(gray, 3)
    found = cv2.HoughCircles(
        gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=8, param1=90, param2=12, minRadius=2, maxRadius=14
    )
    if found is None:
        return []
    w, h = _SIZE
    return [(float(cx) / w, float(cy) / h, float(r)) for cx, cy, r in found[0]]


def _model_ready() -> bool:
    return config.ball_model() != "off" and ballmodel.available()


def candidates(frame: Image.Image) -> list[dict]:
    """Roundish, bright, small blobs that could be the ball.

    Uses the trained ONNX detector when one is installed (``ball.onnx``), else the
    colour/shape heuristic.
    """
    if _model_ready():
        out = []
        for d in ballmodel.detect(frame):
            area = int(((d["x2"] - d["x1"]) * _SIZE[0]) * ((d["y2"] - d["y1"]) * _SIZE[1]))
            out.append(
                {
                    "cx": round((d["x1"] + d["x2"]) / 2, 3),
                    "cy": round((d["y1"] + d["y2"]) / 2, 3),
                    "area": max(_MIN_AREA, area),
                    "src": "model",
                    "score": d.get("score"),
                }
            )
        return out

    mask = _color_mask(frame)
    out: list[dict] = []
    for comp in cvutil.components(mask):
        area = comp["area"]
        if area < _MIN_AREA or area > _MAX_AREA:
            continue
        x0, y0, x1, y1 = comp["bbox"]
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        aspect = bw / max(bh, 1)
        fill = area / max(bw * bh, 1)
        if 0.4 <= aspect <= 2.5 and fill >= 0.4:
            out.append({"cx": comp["cx"], "cy": comp["cy"], "area": area, "src": "blob"})

    # A Hough circle only counts if it sits on ball-coloured pixels (fewer false positives).
    h, w = mask.shape
    for cx, cy, r in _circles(frame):
        px = min(w - 1, max(0, int(cx * w)))
        py = min(h - 1, max(0, int(cy * h)))
        if not mask[py, px]:
            continue
        area = int(math.pi * max(r, 1) ** 2)
        if _MIN_AREA <= area <= _MAX_AREA:
            out.append({"cx": round(cx, 3), "cy": round(cy, 3), "area": area, "src": "circle"})
    return out


def _predict(track: dict) -> tuple[float, float]:
    pts = track["points"]
    if len(pts) >= 2 and track.get("vx") is not None:
        return pts[-1]["cx"] + track["vx"], pts[-1]["cy"] + track["vy"]
    return pts[-1]["cx"], pts[-1]["cy"]


def track(frames: list[Image.Image], timestamps: list[float]) -> list[dict]:
    """Constant-velocity nearest-neighbour tracking; returns time-ordered tracks."""
    tracks: list[dict] = []
    finished: list[dict] = []
    for i, frame in enumerate(frames):
        cands = candidates(frame)
        for tr in tracks:
            tr["matched"] = False
        # Match the closest candidate to each track's predicted next position.
        for tr in tracks:
            if tr["matched"]:
                continue
            px, py = _predict(tr)
            best, best_d = None, _MAX_STEP
            for cand in cands:
                if cand.get("used"):
                    continue
                d = math.hypot(px - cand["cx"], py - cand["cy"])
                if d < best_d:
                    best_d, best = d, cand
            if best is not None:
                best["used"] = True
                _append(tr, best, timestamps[i])
        for cand in cands:
            if not cand.get("used"):
                tracks.append(
                    {
                        "points": [{"t": round(float(timestamps[i]), 2), "cx": cand["cx"], "cy": cand["cy"], "area": cand["area"]}],
                        "vx": None,
                        "vy": None,
                        "matched": True,
                        "missed": 0,
                    }
                )
        for tr in tracks:
            if not tr["matched"]:
                tr["missed"] += 1
        # Once a track has been missing too long, finalize it (don't discard the
        # evidence) — the ball often leaves the frame between rallies.
        still: list[dict] = []
        for tr in tracks:
            if tr["missed"] > _MAX_MISSED:
                finished.append(tr)
            else:
                still.append(tr)
        tracks = still
    finished.extend(tracks)
    finished = [tr for tr in finished if len(tr["points"]) >= 3 and _travel(tr) >= _MIN_TRAVEL]
    finished.sort(key=lambda tr: len(tr["points"]), reverse=True)
    return finished


def _travel(tr: dict) -> float:
    """Largest extent of a track (x or y range) — used to drop static false positives."""
    points = tr.get("points") or []
    if not points:
        return 0.0
    xs = [p["cx"] for p in points]
    ys = [p["cy"] for p in points]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def _append(tr: dict, cand: dict, t: float) -> None:
    prev = tr["points"][-1]
    vx = cand["cx"] - prev["cx"]
    vy = cand["cy"] - prev["cy"]
    # Smooth the velocity a little so one noisy point doesn't throw the prediction.
    tr["vx"] = vx if tr.get("vx") is None else 0.6 * vx + 0.4 * tr["vx"]
    tr["vy"] = vy if tr.get("vy") is None else 0.6 * vy + 0.4 * tr["vy"]
    tr["points"].append({"t": round(float(t), 2), "cx": cand["cx"], "cy": cand["cy"], "area": cand["area"]})
    tr["matched"] = True
    tr["missed"] = 0


def _speed_profile(points: list[dict]) -> list[float]:
    out: list[float] = []
    for i in range(1, len(points)):
        dt = max(1e-3, points[i]["t"] - points[i - 1]["t"])
        out.append(math.hypot(points[i]["cx"] - points[i - 1]["cx"], points[i]["cy"] - points[i - 1]["cy"]) / dt)
    return out


def _reversals(points: list[dict], axis: str) -> list[float]:
    """Times where the track reverses on ``axis`` ('x' hit, 'y' bounce)."""
    key = "cx" if axis == "x" else "cy"
    events: list[float] = []
    for i in range(2, len(points)):
        v1 = points[i - 1][key] - points[i - 2][key]
        v2 = points[i][key] - points[i - 1][key]
        if v1 * v2 < 0 and abs(v1) > 0.005 and abs(v2) > 0.005:
            events.append(points[i]["t"])
    return events


def contacts(main_track: dict) -> list[float]:
    """Times where the tracked ball reverses direction (hit/bounce proxy)."""
    return _reversals(main_track["points"], "x")


def trajectory3d(main_track: dict) -> list[dict]:
    """Shallow 3D path: (x, y) as seen plus a depth ``z`` from apparent blob size.

    Depth is *relative* (monocular): bigger blob = nearer. ``z`` is normalized so
    the median sits at 1.0. Heuristic — direction of depth change is meaningful,
    absolute distance is not.
    """
    pts = [p for p in main_track["points"] if p.get("area")]
    if len(pts) < 3:
        return []
    areas = sorted(p["area"] for p in pts)
    ref = areas[len(areas) // 2] or 1.0
    out: list[dict] = []
    for p in pts:
        z = round(math.sqrt(ref / max(p["area"], 1)), 3)
        out.append({"t": p["t"], "x": p["cx"], "y": p["cy"], "z": z})
    return out


def overlay(frames: list[Image.Image], info: dict) -> Image.Image | None:
    """Draw the main ball path over the middle frame of the track."""
    tracks = info.get("tracks") or []
    if not frames or not tracks:
        return None
    main = tracks[0].get("points") or []
    if len(main) < 2:
        return None
    base = frames[min(range(len(frames)), key=lambda i: abs(i - len(frames) // 2))].convert("RGB").copy()
    w, h = base.size
    draw = ImageDraw.Draw(base)
    xy = [(int(p["cx"] * w), int(p["cy"] * h)) for p in main]
    if len(xy) >= 2:
        draw.line(xy, fill=(56, 189, 248), width=max(2, w // 320))
    for i, (x, y) in enumerate(xy):
        r = max(3, w // 160)
        colour = (249, 115, 22) if i == len(xy) - 1 else (56, 189, 248)
        draw.ellipse((x - r, y - r, x + r, y + r), outline=colour, width=max(2, w // 480))
    return base


def rally_segments(activity: list[dict], timestamps: list[float]) -> list[dict]:
    """Contiguous spans where movement energy is clearly above the pause level."""
    energies = [s["energy"] for s in activity]
    if not energies:
        return []
    baseline = float(np.median(energies)) or 0.0
    threshold = max(baseline * 1.3, baseline + 0.5)
    segments: list[dict] = []
    start = None
    for s in activity:
        active = s["energy"] >= threshold
        if active and start is None:
            start = s["t"]
        elif not active and start is not None:
            segments.append({"start": start, "end": s["t"]})
            start = None
    if start is not None:
        end = round(float(timestamps[-1]), 2) if timestamps else start
        segments.append({"start": start, "end": end})
    return [seg for seg in segments if seg["end"] - seg["start"] >= 0.4]


def phase_segments(
    activity: list[dict], timestamps: list[float], contact_times: list[float], bounce_times: list[float]
) -> list[dict]:
    """Active spans labelled by what happened inside them (rally vs. movement)."""
    out: list[dict] = []
    for r in rally_segments(activity, timestamps):
        hits = [round(t, 2) for t in contact_times if r["start"] <= t <= r["end"]]
        bounces = [round(t, 2) for t in bounce_times if r["start"] <= t <= r["end"]]
        if hits:
            label = f"Rally · {len(hits)} contact(s)"
        elif bounces:
            label = f"Bounce play · {len(bounces)}"
        else:
            label = "Movement"
        out.append({"start": r["start"], "end": r["end"], "label": label, "contacts": hits, "bounces": bounces})
    return out


def detect(frames: list[Image.Image], timestamps: list[float], activity: list[dict]) -> dict:
    """Aggregate heuristic ball/track/contact/rally information."""
    tracks = track(frames, timestamps)
    main = tracks[0] if tracks else None
    source = "model" if _model_ready() else "heuristic"
    contact_times = contacts(main) if main else []
    bounce_times = _reversals(main["points"], "y") if main else []
    rallies = rally_segments(activity, timestamps)
    visible = len({p["t"] for p in (main["points"] if main else [])})
    speeds = _speed_profile(main["points"]) if main and len(main["points"]) > 1 else []
    traj = trajectory3d(main) if main else []
    segments = phase_segments(activity, timestamps, contact_times, bounce_times)

    stats = {
        "visible_frames": visible,
        "max_speed": round(max(speeds), 4) if speeds else 0.0,
        "mean_speed": round(sum(speeds) / len(speeds), 4) if speeds else 0.0,
        "hits": [round(t, 2) for t in contact_times],
        "bounces": [round(t, 2) for t in bounce_times],
    }
    if main and main["points"]:
        xs = [p["cx"] for p in main["points"]]
        ys = [p["cy"] for p in main["points"]]
        stats["x_range"] = round(max(xs) - min(xs), 3)
        stats["y_range"] = round(max(ys) - min(ys), 3)

    if not main and not rallies:
        summary = f"no ball-like object or rally segments detected ({source}, low confidence)"
    else:
        bits = []
        if main:
            bits.append(f"ball tracked in {visible} frames (max speed {stats['max_speed']}/s)")
        if contact_times:
            bits.append(f"~{len(contact_times)} hit reversal(s)")
        if bounce_times:
            bits.append(f"~{len(bounce_times)} bounce reversal(s)")
        if rallies:
            bits.append("rally segment(s) " + ", ".join(f"{r['start']}-{r['end']}s" for r in rallies))
        summary = "; ".join(bits) + f" ({source}, low confidence)"

    return {
        "summary": summary,
        "detector": "onnx-model" if _model_ready() else ("cv2+hough" if cv2 is not None else "blob"),
        "tracks": [{"points": t["points"]} for t in tracks[:3]],
        "contacts": contact_times,
        "bounces": bounce_times,
        "rallies": rallies,
        "segments": segments,
        "stats": stats,
        "trajectory3d": traj,
    }
