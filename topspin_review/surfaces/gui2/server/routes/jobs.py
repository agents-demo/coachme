"""Job lifecycle: list, status, cancel, retry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/jobs")
def jobs() -> dict:
    from topspin_review.surfaces.gui2.server.jobs import get_manager

    return {"jobs": get_manager().jobs()}


@router.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    from topspin_review.surfaces.gui2.server.jobs import get_manager

    status = get_manager().status(job_id)
    if status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="unknown job")
    return status


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    from topspin_review.surfaces.gui2.server.jobs import get_manager

    return {"cancelled": get_manager().cancel(job_id)}


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    from topspin_review.surfaces.gui2.server.jobs import get_manager

    new_id = get_manager().retry(job_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return {"job_id": new_id, "status_url": f"/jobs/{new_id}"}
