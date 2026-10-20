"""Job lifecycle: list, status, cancel, retry, and SSE stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.get("/jobs")
def jobs() -> dict:
    from coachme.surfaces.gui2.server.jobs import get_manager

    return {"jobs": get_manager().jobs()}


@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str) -> StreamingResponse:
    """Server-Sent Events stream of job progress until completion.

    The client connects once and receives a ``data:`` JSON event every ~600 ms
    until the job reaches ``done``, ``failed`` or ``cancelled``.  A final
    ``event: close`` frame is sent so the client knows to close its
    ``EventSource``.
    """
    from coachme.surfaces.gui2.server.jobs import get_manager

    manager = get_manager()

    async def generate():
        while True:
            status = manager.status(job_id)
            if status.get("status") == "unknown":
                yield f"event: error\ndata: {json.dumps({'error': 'unknown job'})}\n\n"
                return
            yield f"data: {json.dumps(status)}\n\n"
            if status["status"] in ("done", "failed", "cancelled"):
                yield "event: close\ndata: {}\n\n"
                return
            await asyncio.sleep(0.6)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/jobs/{job_id}")
def job_status(job_id: str) -> dict:
    from coachme.surfaces.gui2.server.jobs import get_manager

    status = get_manager().status(job_id)
    if status.get("status") == "unknown":
        raise HTTPException(status_code=404, detail="unknown job")
    return status


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str) -> dict:
    from coachme.surfaces.gui2.server.jobs import get_manager

    return {"cancelled": get_manager().cancel(job_id)}


@router.post("/jobs/{job_id}/retry")
def retry_job(job_id: str) -> dict:
    from coachme.surfaces.gui2.server.jobs import get_manager

    new_id = get_manager().retry(job_id)
    if new_id is None:
        raise HTTPException(status_code=404, detail="unknown job")
    return {"job_id": new_id, "status_url": f"/jobs/{new_id}"}
