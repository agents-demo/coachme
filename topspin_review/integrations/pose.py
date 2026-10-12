"""Real pose estimation via ``mediapipe`` (Tasks API).

Uses mediapipe's ``PoseLandmarker`` (the modern Tasks API, available in mediapipe
1.x). The small landmarker model is downloaded on first use into
``runtime/data/models/`` and cached. When the Tasks API is unavailable, callers fall
back to the dependency-free region proxy in :mod:`topspin_review.core.video.metrics`.
"""

from __future__ import annotations

import math
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from topspin_review.integrations.storage import runtime

_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

# mediapipe Pose landmark indices.
_L = {
    "l_shoulder": 11,
    "r_shoulder": 12,
    "l_elbow": 13,
    "r_elbow": 14,
    "l_wrist": 15,
    "r_wrist": 16,
    "l_hip": 23,
    "r_hip": 24,
    "l_knee": 25,
    "r_knee": 26,
    "l_ankle": 27,
    "r_ankle": 28,
}

# Skeleton edges drawn by :func:`overlay` (subset of mediapipe's connections).
_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
]


def _tasks():
    """Return ``(mp, BaseOptions, vision)`` for the Tasks API, or ``None`` if unavailable."""
    try:
        import mediapipe as mp
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        return mp, mp_python.BaseOptions, vision
    except Exception:
        return None


def available() -> bool:
    """True when mediapipe's Tasks PoseLandmarker API can be imported."""
    return _tasks() is not None


def _model_path() -> Path:
    return runtime.DATA_DIR / "models" / "pose_landmarker_lite.task"


def _ensure_model() -> str | None:
    """Return the landmarker model path, downloading it once if needed."""
    path = _model_path()
    if path.exists() and path.stat().st_size > 0:
        return str(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(_MODEL_URL, path)
    except Exception:
        return None
    return str(path) if path.exists() and path.stat().st_size > 0 else None


def _angle(a, b, c) -> float:
    ax, ay = a
    bx, by = b
    cx, cy = c
    v1 = (ax - bx, ay - by)
    v2 = (cx - bx, cy - by)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return round(math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2))))), 1)


def _angle3d(a, b, c) -> float:
    v1 = (a[0] - b[0], a[1] - b[1], a[2] - b[2])
    v2 = (c[0] - b[0], c[1] - b[1], c[2] - b[2])
    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    n1 = math.sqrt(sum(x * x for x in v1))
    n2 = math.sqrt(sum(x * x for x in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return round(math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2))))), 1)


def _torso_lean(ls, rs, lh, rh) -> float:
    """Angle of the shoulder→hip line from vertical (degrees)."""
    sx, sy, sz = (ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2, (ls[2] + rs[2]) / 2
    hx, hy, hz = (lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2, (lh[2] + rh[2]) / 2
    vx, vy, vz = sx - hx, sy - hy, sz - hz
    n = math.sqrt(vx * vx + vy * vy + vz * vz) or 1.0
    # world y points down, so "up" is (0, -1, 0)
    cos = max(-1.0, min(1.0, -vy / n))
    return round(math.degrees(math.acos(cos)), 1)


def _twist(left, right) -> float:
    """Rotation of a left→right line in the transverse (x–z) plane (degrees)."""
    return round(math.degrees(math.atan2(right[2] - left[2], right[0] - left[0])), 1)


_KEYS3D = ("l_knee_3d", "r_knee_3d", "l_elbow_3d", "r_elbow_3d", "torso_lean", "shoulder_twist", "hip_twist")


def estimate(frames: list[Image.Image]) -> list[dict] | None:
    """Per-frame joint metrics, or ``None`` when pose estimation is unavailable."""
    api = _tasks()
    if api is None:
        return None
    mp, BaseOptions, vision = api
    model = _ensure_model()
    if model is None:
        return None

    try:
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
        )
        landmarker = vision.PoseLandmarker.create_from_options(options)
    except Exception:
        return None

    out: list[dict] = []
    with landmarker:
        for frame in frames:
            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(frame.convert("RGB")))
                result = landmarker.detect(mp_image)
                poses = getattr(result, "pose_landmarks", None)
            except Exception:
                poses = None
            if not poses:
                out.append({})
                continue
            lm = poses[0]
            vis = [float(getattr(p, "visibility", 0.0) or 0.0) or float(getattr(p, "presence", 0.0) or 0.0) for p in lm]
            if not any(vis):
                vis = [1.0] * len(lm)  # Tasks model may omit visibility; draw anyway
            pt = {name: (lm[idx].x, lm[idx].y) for name, idx in _L.items()}
            entry: dict = {
                "l_knee": _angle(pt["l_hip"], pt["l_knee"], pt["l_ankle"]),
                "r_knee": _angle(pt["r_hip"], pt["r_knee"], pt["r_ankle"]),
                "l_elbow": _angle(pt["l_shoulder"], pt["l_elbow"], pt["l_wrist"]),
                "r_elbow": _angle(pt["r_shoulder"], pt["r_elbow"], pt["r_wrist"]),
                "stance_width": round(abs(pt["l_ankle"][0] - pt["r_ankle"][0]), 3),
                "crouch": round((pt["l_hip"][1] + pt["r_hip"][1]) / 2 - (pt["l_ankle"][1] + pt["r_ankle"][1]) / 2, 3),
                "landmarks": [(p.x, p.y, v) for p, v in zip(lm, vis)],
            }
            world = getattr(result, "pose_world_landmarks", None)
            if world:
                wl = world[0]
                wp = {name: (wl[idx].x, wl[idx].y, wl[idx].z) for name, idx in _L.items()}
                entry.update(
                    {
                        "l_knee_3d": _angle3d(wp["l_hip"], wp["l_knee"], wp["l_ankle"]),
                        "r_knee_3d": _angle3d(wp["r_hip"], wp["r_knee"], wp["r_ankle"]),
                        "l_elbow_3d": _angle3d(wp["l_shoulder"], wp["l_elbow"], wp["l_wrist"]),
                        "r_elbow_3d": _angle3d(wp["r_shoulder"], wp["r_elbow"], wp["r_wrist"]),
                        "torso_lean": _torso_lean(wp["l_shoulder"], wp["r_shoulder"], wp["l_hip"], wp["r_hip"]),
                        "shoulder_twist": _twist(wp["l_shoulder"], wp["r_shoulder"]),
                        "hip_twist": _twist(wp["l_hip"], wp["r_hip"]),
                    }
                )
            out.append(entry)
    return out


def overlay(frames: list[Image.Image], pose: list | None) -> list[Image.Image]:
    """Draw the skeleton on each frame (no-op without landmarks)."""
    if not pose:
        return []
    out: list[Image.Image] = []
    for frame, p in zip(frames, pose):
        img = frame.copy()
        landmarks = (p or {}).get("landmarks")
        if landmarks:
            w, h = img.size
            draw = ImageDraw.Draw(img)
            for a, b in _CONNECTIONS:
                if a >= len(landmarks) or b >= len(landmarks):
                    continue
                xa, ya, va = landmarks[a]
                xb, yb, vb = landmarks[b]
                if va < 0.4 or vb < 0.4:
                    continue
                draw.line([(xa * w, ya * h), (xb * w, yb * h)], fill=(0, 255, 60), width=max(2, w // 320))
            for x, y, vis in landmarks:
                if vis < 0.4:
                    continue
                r = max(2, w // 400)
                draw.ellipse([x * w - r, y * h - r, x * w + r, y * h + r], fill=(255, 90, 0))
        out.append(img)
    return out


def summarize(pose: list[dict] | None) -> dict:
    if not pose:
        return {}
    valid = [p for p in pose if p]
    if not valid:
        return {}
    keys = ("l_knee", "r_knee", "l_elbow", "r_elbow", "stance_width", "crouch")
    summary = {}
    for k in keys:
        values = [p[k] for p in valid if k in p]
        if values:
            summary[f"{k}_mean"] = round(sum(values) / len(values), 2)
            summary[f"{k}_range"] = round(max(values) - min(values), 2)
    return summary


def summarize3d(pose: list[dict] | None) -> dict:
    """Mean/range for the 3D (world-landmark) metrics, when present."""
    if not pose:
        return {}
    valid = [p for p in pose if p and any(k in p for k in _KEYS3D)]
    if not valid:
        return {}
    summary: dict = {}
    for k in _KEYS3D:
        values = [p[k] for p in valid if k in p]
        if values:
            summary[f"{k}_mean"] = round(sum(values) / len(values), 2)
            summary[f"{k}_range"] = round(max(values) - min(values), 2)
    return summary
