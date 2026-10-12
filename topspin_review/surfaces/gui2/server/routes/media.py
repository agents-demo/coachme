"""Media: serve a report's source clip, its analysis artifacts, and its highlight clips."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from topspin_review.integrations.storage import runtime, store
from topspin_review.surfaces.gui2.server import read

router = APIRouter()

_NO_STORE = {"Cache-Control": "no-store, max-age=0"}
_ARTIFACTS = ("frames", "motion", "heatmap", "pose", "pose_hero", "metrics", "observability")


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


@router.get("/callmedia/{stem}/{name}")
def callmedia(stem: str, name: str) -> FileResponse:
    """Serve an image that was sent to the model during a run (saved under <stem>_media/)."""
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise HTTPException(status_code=400, detail="invalid name")
    path = runtime.ARTIFACTS_DIR / f"{stem}_media" / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path, headers=_NO_STORE)


@router.get("/reel/{stem}")
def reel(stem: str) -> FileResponse:
    """Download a highlight reel: the run's key-moment clips stitched into one video."""
    report = store.find_report(stem)
    clips = (report or {}).get("clips") or {}
    if not clips:
        raise HTTPException(status_code=404, detail="no clips to stitch")
    paths = [clips[k] for k in sorted(clips, key=lambda s: float(s))]
    out = runtime.ARTIFACTS_DIR / f"{stem}_reel.mp4"
    if not out.exists():
        from topspin_review.integrations import media

        if not media.make_reel(paths, out):
            raise HTTPException(status_code=500, detail="could not build the reel")
    return FileResponse(out, media_type="video/mp4", headers=_NO_STORE)


@router.get("/cards/{stem}")
def share_card(stem: str) -> Response:
    """A branded share-card PNG for a run."""
    report = store.find_report(stem)
    if not report:
        raise HTTPException(status_code=404, detail="unknown report")
    from topspin_review.integrations import cards

    png = cards.share_card(report)
    if not png:
        raise HTTPException(status_code=500, detail="could not render the card")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})
