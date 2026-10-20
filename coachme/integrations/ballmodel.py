"""Trained ball detector (YOLOv8-nano, ONNX Runtime) — optional, with no-op fallback.

If a model file exists at ``runtime/data/models/ball.onnx`` (override with
``BALL_MODEL_PATH``), :func:`detect` runs it per frame and returns normalized
ball boxes; otherwise :func:`available` is ``False`` and the caller falls back to
the heuristic in :mod:`coachme.core.stages.measure.ball`.

The model is a standard single-class ball export: YOLOv8 ``1x3xSxS`` → ``1x(D)xN`` or
YOLOv5 ``1x3xSxS`` → ``1xNx(D)``, boxes as ``cx, cy, w, h`` in input pixels. Both
layouts are auto-detected (override with ``BALL_MODEL_FAMILY``). Export the trained
model to that path — see ``scripts/train_ball.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image

from coachme.integrations.storage import runtime

_DEFAULT_IMGSZ = 640
_STRIDE = 32
_PAD = 114  # Ultralytics letterbox fill


def _model_path() -> Path:
    override = os.getenv("BALL_MODEL_PATH", "").strip()
    if override:
        return Path(override)
    return runtime.DATA_DIR / "models" / "ball.onnx"


def _imgsz() -> int:
    return int(os.getenv("BALL_MODEL_IMGSZ", str(_DEFAULT_IMGSZ)))


_session_cache: dict[str, object] = {}


def _session():
    """Return a cached ONNX Runtime session, or ``None`` if unavailable."""
    path = _model_path()
    key = str(path)
    if key in _session_cache:
        return _session_cache[key]
    session = None
    if path.exists() and path.stat().st_size > 0:
        try:
            import onnxruntime as ort

            session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        except Exception:
            session = None
    _session_cache[key] = session
    return session


def available() -> bool:
    """True when a model file is present and ONNX Runtime can load it."""
    return _session() is not None


def _letterbox(img: Image.Image, size: int) -> tuple[np.ndarray, float, tuple[float, float]]:
    """Resize with aspect preserved + grey pad to ``size``; return CHW tensor, ratio, (padx, pady)."""
    w, h = img.size
    ratio = min(size / w, size / h)
    new_w, new_h = max(1, round(w * ratio)), max(1, round(h * ratio))
    resized = img.convert("RGB").resize((new_w, new_h), Image.BILINEAR)
    canvas = Image.new("RGB", (size, size), (_PAD, _PAD, _PAD))
    padx, pady = (size - new_w) / 2, (size - new_h) / 2
    canvas.paste(resized, (int(round(padx)), int(round(pady))))
    arr = np.asarray(canvas, dtype=np.float32) / 255.0
    chw = np.transpose(arr, (2, 0, 1))[None, ...]
    return chw, ratio, (padx, pady)


def _nms(boxes: np.ndarray, scores: np.ndarray, iou: float) -> list[int]:
    """Class-agnostic greedy NMS; returns kept indices (descending score)."""
    if boxes.size == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]
    keep: list[int] = []
    while order.size > 0:
        i = int(order[0])
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        union = areas[i] + areas[order[1:]] - inter
        iou_vals = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        order = order[1:][iou_vals <= iou]
    return keep


def _decode(out: np.ndarray, conf: float, iou: float, family: str = "auto") -> tuple[np.ndarray, np.ndarray]:
    """Parse a YOLO output tensor into ``(boxes_xyxy, scores)`` after conf + NMS.

    Handles both export layouts: YOLOv8 ``(1, 4+nc, N)`` (no objectness) and YOLOv5
    ``(1, N, 5+nc)`` (objectness column). In ``auto`` mode a single-class ball model
    with ``D >= 6`` channels is read as v5, ``D == 5`` (or fewer) as v8; override with
    the ``BALL_MODEL_FAMILY`` env var (``yolov5``/``yolov8``).
    """
    arr = np.asarray(out)
    arr = np.squeeze(arr)
    if arr.ndim != 2:
        return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    # Orient to (N, D): v8 ships (D, N), v5 ships (N, D); D is the small dimension.
    if arr.shape[0] < arr.shape[1]:
        arr = arr.T
    if family == "auto":
        family = "yolov5" if arr.shape[1] >= 6 else "yolov8"

    boxes_xywh = arr[:, :4]
    if family == "yolov5":
        obj = arr[:, 4]
        cls = arr[:, 5:]
        cls_conf = obj * (cls.max(axis=1) if cls.shape[1] else 1.0)
    else:
        cls = arr[:, 4:]
        if cls.shape[1] == 0:
            return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32)
        cls_conf = cls.max(axis=1)

    mask = cls_conf >= conf
    boxes_xywh = boxes_xywh[mask]
    cls_conf = cls_conf[mask]
    if boxes_xywh.shape[0] == 0:
        return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    cx, cy, w, h = boxes_xywh[:, 0], boxes_xywh[:, 1], boxes_xywh[:, 2], boxes_xywh[:, 3]
    xyxy = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1).astype(np.float32)
    keep = _nms(xyxy, cls_conf.astype(np.float32), iou)
    return xyxy[keep], cls_conf[keep].astype(np.float32)


def detect(img: Image.Image, conf: float | None = None, iou: float = 0.45) -> list[dict]:
    """Detect the ball in one frame; return normalized ``x1,y1,x2,y2,score`` boxes."""
    session = _session()
    if session is None:
        return []
    conf = float(os.getenv("BALL_MODEL_CONF", "0.25")) if conf is None else conf
    w, h = img.size
    tensor, ratio, (padx, pady) = _letterbox(img, _imgsz())
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: tensor})
    family = os.getenv("BALL_MODEL_FAMILY", "auto").strip().lower()
    boxes, scores = _decode(outputs[0], conf, iou, family)
    out: list[dict] = []
    for (x1, y1, x2, y2), score in zip(boxes, scores):
        nx1 = max(0.0, min(1.0, (float(x1) - padx) / ratio / w))
        ny1 = max(0.0, min(1.0, (float(y1) - pady) / ratio / h))
        nx2 = max(0.0, min(1.0, (float(x2) - padx) / ratio / w))
        ny2 = max(0.0, min(1.0, (float(y2) - pady) / ratio / h))
        if nx2 <= nx1 or ny2 <= ny1:
            continue
        out.append({"x1": round(nx1, 4), "y1": round(ny1, 4), "x2": round(nx2, 4), "y2": round(ny2, 4), "score": round(float(score), 3)})
    return out
