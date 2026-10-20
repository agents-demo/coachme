"""Analysis submission: synchronous and queued."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from coachme.core import service
from coachme.core.bootstrap import setup
from coachme.surfaces.gui2.server.models import AnalyzeRequest

router = APIRouter()


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    """Run the analysis synchronously and return the report (blocks until done)."""
    setup()
    if not Path(request.video_path).exists():
        raise HTTPException(status_code=400, detail=f"file not found: {request.video_path}")
    try:
        outcome = service.analyze_video_sync(
            request.video_path,
            region_box=service.parse_region_box(request.region_box),
            language=request.language,
            mode=request.mode or ("agentic" if request.agentic else None),
        )
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    return {"report_path": outcome.get("report_path"), "report": outcome.get("report")}


@router.post("/analyze/async")
def analyze_async(request: AnalyzeRequest) -> dict:
    """Enqueue an analysis; poll it at ``/jobs/{id}``."""
    setup()
    if not Path(request.video_path).exists():
        raise HTTPException(status_code=400, detail=f"file not found: {request.video_path}")
    from coachme.surfaces.gui2.server.jobs import get_manager

    job_id = get_manager().submit(
        request.video_path,
        region_box=service.parse_region_box(request.region_box),
        agentic=request.agentic,
        language=request.language,
        mode=request.mode,
    )
    return {"job_id": job_id, "status_url": f"/jobs/{job_id}"}
