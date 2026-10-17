"""Reports: list, one report, ask, and compare."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from topspin_review.core import service
from topspin_review.domain import annotations as annotations_schema
from topspin_review.domain import compare as compare_mod
from topspin_review.integrations import reporting
from topspin_review.integrations.storage import store
from topspin_review.surfaces.gui2.server import read

router = APIRouter()


class AnnotationsRequest(BaseModel):
    annotations: list[dict] = []


class FeedbackRequest(BaseModel):
    item: str = "session"  # issue text, or "session" for a session-level vote
    vote: str  # "up" or "down"
    note: str = ""


@router.get("/reports")
def reports() -> dict:
    return {"reports": read.list_reports()}


@router.get("/reports/{stem}")
def report(stem: str) -> dict:
    found = read.get_report(stem)
    if found is None:
        raise HTTPException(status_code=404, detail="unknown report")
    return found


@router.delete("/reports/{stem}")
def delete_report(stem: str) -> dict:
    """Delete a session's report and its artifacts/exports/cache."""
    if read.get_report(stem) is None:
        raise HTTPException(status_code=404, detail="unknown report")
    return {"deleted": store.delete_report(stem)}


@router.post("/reports/{stem}/feedback")
def add_feedback(stem: str, payload: FeedbackRequest) -> dict:
    """Record a 👍/👎 vote on a session or a specific issue.

    Votes are appended (never overwritten) so the full history is kept for
    prompt-improvement work.  ``item`` is the issue text or ``"session"`` for a
    session-level vote.
    """
    if payload.vote not in ("up", "down"):
        raise HTTPException(status_code=400, detail="vote must be 'up' or 'down'")
    if read.get_report(stem) is None:
        raise HTTPException(status_code=404, detail="unknown report")
    result = store.append_feedback(stem, payload.item, payload.vote, payload.note)
    return {"feedback": result}


@router.post("/reports/{stem}/annotations")
def save_annotations(stem: str, payload: AnnotationsRequest) -> dict:
    """Persist on-frame shape annotations (arrow / line / circle / pen) for a report."""
    if read.get_report(stem) is None:
        raise HTTPException(status_code=404, detail="unknown report")
    items = annotations_schema.normalize(payload.annotations)
    store.set_annotations(stem, items)
    return {"annotations": items}


@router.get("/reports/{stem}/ask")
def ask(stem: str, q: str, language: str = "en") -> dict:
    if not q.strip():
        raise HTTPException(status_code=400, detail="empty question")
    if read.get_report(stem) is None:
        raise HTTPException(status_code=404, detail="unknown report")
    return {"answer": service.ask_sync(stem, q, language=language)}


@router.get("/compare")
def compare(a: str, b: str) -> dict:
    older, newer = store.find_report(a), store.find_report(b)
    if not older or not newer:
        raise HTTPException(status_code=404, detail="one of the reports is unknown")
    return compare_mod.compare(older, newer)


@router.get("/export/{stem}/{fmt}")
def export(stem: str, fmt: str):
    """Render a report to Markdown or HTML for download."""
    report = store.find_report(stem)
    if not report:
        raise HTTPException(status_code=404, detail="unknown report")
    if fmt == "md":
        return PlainTextResponse(reporting.to_markdown(report), media_type="text/markdown")
    if fmt == "html":
        return HTMLResponse(reporting.to_html(report))
    raise HTTPException(status_code=400, detail="fmt must be md or html")
