"""HTTP server for gui2: submit a clip, track jobs, read reports, serve media + the SPA.

    uvicorn topspin_review.surfaces.gui2:app
    # then open http://localhost:8000/gui2/
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from topspin_review.surfaces.gui2.server import config
from topspin_review.surfaces.gui2.server.routes import analyze, ingest, jobs, media, reports
from topspin_review.surfaces.readiness import checks as readiness_checks

app = FastAPI(title="Topspin Review")

# Allow the SvelteKit dev server (5174) to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)
app.include_router(reports.router)
app.include_router(jobs.router)
app.include_router(media.router)
app.include_router(ingest.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/ready")
def ready() -> dict:
    """Environment readiness (model / vision / pose / pdf / sample) for the UI."""
    return {"checks": readiness_checks()}


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/gui2/" if config.CLIENT_BUILD.exists() else "/health")


@app.get("/gui2/{path:path}")
@app.get("/gui2")
def spa(path: str = "") -> FileResponse:
    """Serve the built gui2 SPA, falling back to index.html for client routes."""
    root = config.CLIENT_BUILD.resolve()
    candidate = (root / path).resolve()
    if path and candidate.is_file() and str(candidate).startswith(str(root)):
        return FileResponse(candidate)
    return FileResponse(root / "index.html")
