"""Environment readiness checks surfaced by the app.

Light: reads env vars directly (no heavy backend import) plus a couple of cheap
probes, so a run can be started with confidence (or a clear reason it will fail).
"""

from __future__ import annotations

import importlib.util
import os

from dotenv import load_dotenv

from topspin_review.integrations.storage import runtime

load_dotenv()


def _model_ok() -> bool:
    return all(os.getenv(k) for k in ("API_KEY", "API_BASE", "MODEL_NAME"))


def checks() -> list[dict]:
    """The readiness checks, in display order."""
    model_ok = _model_ok()
    vision_name = os.getenv("VISION_MODEL_NAME") or "deepseek-v4-flash-vision-exp"
    pose_ok = importlib.util.find_spec("mediapipe") is not None
    pdf_ok = importlib.util.find_spec("reportlab") is not None
    clip = runtime.DATA_DIR / "sample.mp4"
    return [
        {
            "name": "model",
            "ok": model_ok,
            "detail": os.getenv("MODEL_NAME") or "set API_KEY / API_BASE / MODEL_NAME in .env",
        },
        {
            "name": "vision",
            "ok": bool(os.getenv("VISION_MODEL_NAME")),
            "detail": vision_name,
        },
        {
            "name": "pose",
            "ok": pose_ok,
            "detail": "mediapipe" if pose_ok else "pip install -r requirements.txt (mediapipe)",
        },
        {
            "name": "pdf",
            "ok": pdf_ok,
            "detail": "reportlab" if pdf_ok else "pip install -r requirements.txt (reportlab)",
        },
        {
            "name": "sample",
            "ok": clip.exists(),
            "detail": "sample clip ready" if clip.exists() else "missing runtime/data/sample.mp4",
        },
    ]


def ready() -> bool:
    return all(c["ok"] for c in checks())
