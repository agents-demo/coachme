"""Ingest: upload a clip/photo and list the local sample clips."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from topspin_review.core.bootstrap import setup
from topspin_review.integrations.storage import runtime
from topspin_review.surfaces.gui2.server import config

router = APIRouter()


@router.post("/upload")
def upload(file: UploadFile = File(...)) -> dict:  # noqa: B008  (FastAPI dependency idiom)
    """Save an uploaded video/photo and return its server-side path (for ``/analyze/async``)."""
    setup()
    name = Path(file.filename or "").name
    suffix = Path(name).suffix.lower()
    if suffix not in config.ACCEPTED:
        raise HTTPException(status_code=400, detail=f"unsupported file type: {suffix or 'unknown'}")
    dest_dir = config.UPLOADS / uuid.uuid4().hex[:12]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (name or f"clip{suffix}")
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return {"path": str(dest), "name": dest.name}


@router.get("/samples")
def samples() -> dict:
    """Local clips you can analyze without uploading (the synthetic sample, plus uploads)."""
    out: list[dict] = []
    sample = runtime.DATA_DIR / "sample.mp4"
    if sample.exists():
        out.append({"name": "sample", "title": "Built-in sample (synthetic table tennis)", "path": str(sample)})
    if config.UPLOADS.is_dir():
        for path in sorted(config.UPLOADS.rglob("*")):
            if path.is_file() and path.suffix.lower() in config.ACCEPTED:
                out.append({"name": path.name, "title": f"Uploaded · {path.name}", "path": str(path)})
    return {"samples": out}
