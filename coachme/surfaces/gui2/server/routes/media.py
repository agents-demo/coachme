"""Media: serve a report's source clip, its analysis artifacts, and its highlight clips."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from coachme.integrations.storage import runtime, store
from coachme.surfaces.gui2.server import read

router = APIRouter()

_NO_STORE = {"Cache-Control": "no-store, max-age=0"}
_ARTIFACTS = ("frames", "motion", "heatmap", "pose", "pose_hero", "ball", "metrics", "observability")


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
        from coachme.integrations import media

        if not media.make_reel(paths, out):
            raise HTTPException(status_code=500, detail="could not build the reel")
    return FileResponse(out, media_type="video/mp4", headers=_NO_STORE)


@router.get("/trim/{stem}")
def trim(stem: str, start: float, end: float, fmt: str = "mp4", vertical: bool = False) -> FileResponse:
    """Export a trimmed clip (mp4 or gif), optionally cropped 9:16 for socials."""
    if fmt not in ("mp4", "gif"):
        raise HTTPException(status_code=400, detail="fmt must be mp4 or gif")
    report = store.find_report(stem)
    src = (report or {}).get("source")
    if not src or not Path(src).exists():
        raise HTTPException(status_code=404, detail="source not found")
    tag = f"{round(start, 1)}_{round(end, 1)}{'_v' if vertical else ''}"
    out = runtime.ARTIFACTS_DIR / f"{stem}_trim_{tag}.{fmt}"
    if not out.exists():
        from coachme.integrations import media

        if not media.export_clip(src, start, end, out, fmt=fmt, vertical=vertical):
            raise HTTPException(status_code=500, detail="could not export the clip")
    return FileResponse(out, media_type=("image/gif" if fmt == "gif" else "video/mp4"), headers=_NO_STORE)


@router.get("/cards/{stem}")
def share_card(stem: str) -> Response:
    """A branded share-card PNG for a run."""
    report = store.find_report(stem)
    if not report:
        raise HTTPException(status_code=404, detail="unknown report")
    from coachme.integrations import cards

    png = cards.share_card(report)
    if not png:
        raise HTTPException(status_code=500, detail="could not render the card")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": "no-store"})


@router.get("/thumb/{stem}")
def thumb(stem: str) -> FileResponse:
    """A cached square thumbnail centred on the player (pose box, track, or source frame)."""
    report = store.find_report(stem)
    if not report:
        raise HTTPException(status_code=404, detail="unknown report")
    arts = report.get("artifacts") or {}
    metrics = report.get("metrics") or {}
    times = report.get("frame_times") or []
    target = metrics.get("peak_motion_time")
    out = runtime.ARTIFACTS_DIR / f"{stem}_thumb_centered.jpg"
    if out.exists():
        return FileResponse(out, media_type="image/jpeg", headers=_NO_STORE)

    from PIL import Image

    img = None
    hero = arts.get("pose_hero")
    if hero and Path(hero).exists():
        img = Image.open(hero).convert("RGB")
    if img is None:
        source = report.get("source") or ""
        if source and Path(source).exists():
            try:
                from coachme.core.stages.measure import sampling

                if sampling.is_image(source):
                    img = Image.open(source).convert("RGB")
                else:
                    t = float(target or 0.0)
                    frames, _ = sampling.sample_window(source, max(0.0, t - 0.2), t + 0.2, 1)
                    if frames:
                        img = frames[0].convert("RGB")
            except Exception:  # noqa: BLE001
                img = None
    if img is None:
        for kind in ("pose", "motion", "frames"):
            path = arts.get(kind)
            if path and Path(path).exists():
                return FileResponse(path, headers=_NO_STORE)
        raise HTTPException(status_code=404, detail="no thumbnail source")

    # Pick the frame closest to peak motion; keep the original index so pose/track agree.
    idx = None
    if times and target is not None:
        idx = min(range(len(times)), key=lambda i: abs(float(times[i]) - float(target)))
    pose = metrics.get("pose") or []
    boxes = []
    for fr in pose:
        lm = (fr.get("landmarks") or fr.get("lm")) if isinstance(fr, dict) else None
        if not lm:
            boxes.append(None)
            continue
        xs, ys = [], []
        for p in lm:
            if not isinstance(p, (list, tuple)) or len(p) < 3:
                continue
            vis = p[2] if len(p) == 3 else p[3]
            if (vis or 0) >= 0.4:
                xs.append(float(p[0])); ys.append(float(p[1]))
        boxes.append((min(xs), min(ys), max(xs), max(ys)) if xs else None)

    box = boxes[idx] if idx is not None and idx < len(boxes) else None
    if box is None:
        box = next((b for b in boxes if b), None)
    track = metrics.get("track") or []
    tr = track[idx] if idx is not None and idx < len(track) else None
    if box is not None:
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        person_h = max(0.2, box[3] - box[1])
    elif isinstance(tr, dict) and tr.get("cx") is not None:
        cx = float(tr["cx"]); cy = float(tr.get("cy") or 0.5)
        person_h = max(0.2, float(tr.get("h") or 0.6))
    else:
        valid = [b for b in boxes if b]
        if valid:
            cx = sum((b[0] + b[2]) / 2 for b in valid) / len(valid)
            cy = sum((b[1] + b[3]) / 2 for b in valid) / len(valid)
            person_h = max(0.2, sum(b[3] - b[1] for b in valid) / len(valid))
        else:
            cx, cy, person_h = 0.5, 0.5, 0.6

    w_img, h_img = img.size
    side = min(w_img, h_img, max(64, max(round(h_img * 0.65), round(person_h * h_img * 2.0))))
    left = min(max(round(cx * w_img - side / 2), 0), w_img - side)
    top = min(max(round(cy * h_img - side / 2), 0), h_img - side)
    img.crop((left, top, left + side, top + side)).resize((512, 512)).save(out, "JPEG", quality=86)
    return FileResponse(out, media_type="image/jpeg", headers=_NO_STORE)
