"""Media: serve a report's source clip, its analysis artifacts, and its highlight clips."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from topspin_review.surfaces.gui2.server import read

router = APIRouter()

_NO_STORE = {"Cache-Control": "no-store, max-age=0"}
_ARTIFACTS = ("frames", "motion", "pose", "metrics", "observability")


@router.get("/source/{stem}")
def source(stem: str) -> FileResponse:
    """The analyzed video/photo (used as the video the review scrubs)."""
    path = read.source_path(stem)
    if path is None:
        raise HTTPException(status_code=404, detail="source not found")
    return FileResponse(path, headers=_NO_STORE)


@router.get("/artifact/{stem}/{kind}")
def artifact(stem: str, kind: str) -> FileResponse:
    if kind not in _ARTIFACTS:
        raise HTTPException(status_code=400, detail="unknown artifact")
    path = read.artifact_path(stem, kind)
    if path is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    return FileResponse(path, headers=_NO_STORE)


@router.get("/clip/{stem}/{key}")
def clip(stem: str, key: str) -> FileResponse:
    # Clip keys are timestamps like "1.1", so dots are allowed; the key is looked up in the
    # report's clips map (not used as a path), so only separator/empty keys need rejecting.
    if not key or "/" in key or "\\" in key or key in (".", ".."):
        raise HTTPException(status_code=400, detail="invalid clip key")
    path = read.clip_path(stem, key)
    if path is None:
        raise HTTPException(status_code=404, detail="clip not found")
    return FileResponse(path, headers=_NO_STORE)
