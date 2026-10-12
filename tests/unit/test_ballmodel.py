"""Unit tests for the YOLOv8 ONNX ball-model decode/NMS (no model file needed)."""

from __future__ import annotations

import numpy as np

from topspin_review.integrations import ballmodel

_N = 50  # a real Ultralytics export has thousands of anchors; pad to exercise the shape logic


def _yolo_out(boxes_xywh: list[list[float]], scores: list[float]) -> np.ndarray:
    """Build a (1, 4+nc, N) tensor like an Ultralytics export emits (zero-padded anchors)."""
    rows = np.zeros((_N, 5), dtype=np.float32)
    rows[: len(boxes_xywh), :4] = np.asarray(boxes_xywh, dtype=np.float32)
    rows[: len(scores), 4] = np.asarray(scores, dtype=np.float32)
    return rows.T[None, ...]


def test_decode_single_box():
    out = _yolo_out([[100, 100, 20, 20]], [0.9])
    boxes, scores = ballmodel._decode(out, conf=0.25, iou=0.45)
    assert boxes.shape == (1, 4)
    assert abs(boxes[0, 0] - 90) < 1e-3 and abs(boxes[0, 2] - 110) < 1e-3
    assert scores[0] > 0.8


def test_decode_confidence_filter():
    out = _yolo_out([[10, 10, 4, 4], [50, 50, 4, 4]], [0.1, 0.8])
    boxes, _ = ballmodel._decode(out, conf=0.25, iou=0.45)
    assert boxes.shape[0] == 1


def test_decode_nms_dedup():
    out = _yolo_out([[100, 100, 20, 20], [102, 102, 20, 20]], [0.9, 0.8])
    boxes, scores = ballmodel._decode(out, conf=0.25, iou=0.45)
    assert boxes.shape[0] == 1
    assert scores[0] > 0.85


def test_decode_transposed_and_empty():
    out = _yolo_out([[100, 100, 20, 20]], [0.9]).transpose(0, 2, 1)  # (1, N, C)
    boxes, _ = ballmodel._decode(out, conf=0.25, iou=0.45)
    assert boxes.shape == (1, 4)
    empty = ballmodel._decode(np.zeros((1, 5, 0), dtype=np.float32), conf=0.25, iou=0.45)
    assert empty[0].shape[0] == 0
