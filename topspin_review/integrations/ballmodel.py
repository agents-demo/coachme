"""Trained ball detector (YOLOv8-nano, ONNX Runtime) — optional, with no-op fallback.

If a model file exists at ``runtime/data/models/ball.onnx`` (override with
``BALL_MODEL_PATH``), :func:`detect` runs it per frame and returns normalized
ball boxes; otherwise :func:`available` is ``False`` and the caller falls back to
the heuristic in :mod:`topspin_review.core.stages.measure.ball`.

The model is a standard Ultralytics YOLOv8 export (``model.export(format="onnx")``):
input ``1x3xSxS`` RGB float in 0..1; output ``1x(4+nc)xN`` (or transposed),
boxes as ``cx, cy, w, h`` in input pixels and class scores (no objectness).
Export the trained model to that path — see ``scripts/train_ball.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image

from topspin_review.integrations.storage import runtime

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


def _decode(out: np.ndarray, conf: float, iou: float) -> tuple[np.ndarray, np.ndarray]:
    """Parse a YOLOv8 output tensor into ``(boxes_xyxy, scores)`` after conf + NMS."""
    arr = np.asarray(out)
    arr = np.squeeze(arr)
    if arr.ndim != 2:
        return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    # Want shape (N, 4 + nc): the anchor dimension is the long one.
    if arr.shape[0] < arr.shape[1]:
        arr = arr.T
    boxes_xywh = arr[:, :4]
    scores = arr[:, 4:]
    if scores.shape[1] == 0:
        return np.zeros((0, 4), dtype=np.float32), np.zeros((0,), dtype=np.float32)
    cls_conf = scores.max(axis=1)
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
    boxes, scores = _decode(outputs[0], conf, iou)
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
