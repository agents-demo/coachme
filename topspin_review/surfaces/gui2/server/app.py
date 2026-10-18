"""HTTP server for gui2: submit a clip, track jobs, read reports, serve media + the SPA.

    uvicorn topspin_review.surfaces.gui2:app
    # then open http://localhost:8000/gui2/
"""

from __future__ import annotations

import json
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from pydantic import BaseModel

from topspin_review.core import config as app_config
from topspin_review.integrations.agents import settings as agent_settings
from topspin_review.integrations.storage import runtime, store
from topspin_review.surfaces.gui2.server import config
from topspin_review.surfaces.gui2.server.routes import analyze, ingest, jobs, media, reports, trends
from topspin_review.surfaces.readiness import checks as readiness_checks

# Directory containing bundled demo reports (committed to the repo).
_DEMO_DIR = Path(__file__).parents[4] / "demo"


def _seed_demo() -> None:
    """Copy bundled demo reports, videos and artifacts into runtime/data once.

    Seeding happens even when real sessions exist, but the demo never overwrites
    an existing report. A marker prevents a deleted demo from reappearing on the
    next start. The demo is marked so the UI can hide it when real sessions
    exist (see the ``show_demo`` setting).
    """
    data_dir = runtime.DATA_DIR
    marker = data_dir / ".demo_seeded"
    if marker.exists():
        return
    data_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = data_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    for src in _DEMO_DIR.glob("*_report.json"):
        report = json.loads(src.read_text(encoding="utf-8"))
        base_stem = src.stem.removesuffix("_report")
        stem = base_stem
        dst = data_dir / f"{stem}_report.json"
        if dst.exists():
            existing = json.loads(dst.read_text(encoding="utf-8"))
            if existing.get("demo"):
                continue  # already seeded
            # A real session owns this stem; seed the demo under a distinct name.
            stem = f"{base_stem}-Demo"
            dst = data_dir / f"{stem}_report.json"
            if dst.exists():
                continue
        # Copy the companion video if present in demo/.
        video_dst: Path | None = None
        for ext in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
            video_src = _DEMO_DIR / f"{base_stem}{ext}"
            if video_src.exists():
                video_dst = data_dir / f"{stem}{ext}"
                if not video_dst.exists():
                    shutil.copy2(video_src, video_dst)
                break
        if video_dst:
            report["source"] = str(video_dst)
        # Copy generated artifacts (contact sheet, pose, ball, maps).
        artifacts: dict[str, str] = {}
        for kind, name in (report.get("artifacts") or {}).items():
            artifact_src = _DEMO_DIR / Path(str(name)).name
            if not artifact_src.exists():
                continue
            artifact_dst = artifacts_dir / f"{stem}_{kind}{artifact_src.suffix}"
            if not artifact_dst.exists():
                shutil.copy2(artifact_src, artifact_dst)
            artifacts[kind] = str(artifact_dst)
        report["artifacts"] = artifacts
        report["demo"] = True
        report["name"] = report.get("name") or "Demo session"
        dst.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # Keep the demo at the bottom of the mtime-ordered session list.
        try:
            os.utime(dst, (946684800, 946684800))  # 2000-01-01
        except OSError:
            pass
    marker.write_text("ok", encoding="utf-8")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _seed_demo()
    yield


app = FastAPI(title="Topspin Review", lifespan=lifespan)

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
app.include_router(trends.router)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/ready")
def ready() -> dict:
    """Environment readiness (model / vision / pose / pdf / sample) for the UI."""
    return {"checks": readiness_checks()}


class ProfilePayload(BaseModel):
    sport: str = "table tennis"
    level: str = "intermediate"
    dominant_hand: str = "right"
    goal: str = "improve"


@app.get("/profile")
def get_profile() -> dict:
    return store.get_profile()


@app.put("/profile")
def put_profile(payload: ProfilePayload) -> dict:
    profile = store.get_profile()
    profile.pop("hand", None)
    profile.update(payload.model_dump())
    return store.set_profile(profile)


class UiSettingsPayload(BaseModel):
    show_demo: bool | None = None


@app.get("/settings")
def get_ui_settings() -> dict:
    return store.get_ui_settings()


@app.patch("/settings")
def patch_ui_settings(payload: UiSettingsPayload) -> dict:
    return store.set_ui_settings(payload.model_dump(exclude_none=True))


@app.get("/config")
def get_config() -> dict:
    """Read-only, non-secret configuration used by new analyses."""
    return {
        "api_base": agent_settings.api_base(),
        "text_model": agent_settings.text_model_name(),
        "vision_model": agent_settings.vision_model_name(),
        "max_frames": app_config.max_frames(),
        "max_width": app_config.max_width(),
        "zoom_frames": app_config.zoom_frames(),
        "max_windows": app_config.max_windows(),
        "agentic": app_config.agentic_mode(),
        "verify_reports": app_config.verify_reports(),
        "demo_fallback": app_config.demo_fallback(),
    }


@app.get("/")
def index() -> RedirectResponse:
    return RedirectResponse("/gui2/" if config.CLIENT_BUILD.exists() else "/health")


@app.get("/favicon.ico")
def favicon():
    """Serve the SPA favicon (browsers request /favicon.ico at the site root)."""
    svg = config.CLIENT_BUILD / "favicon.svg"
    if svg.is_file():
        return FileResponse(svg, media_type="image/svg+xml")
    return Response(status_code=204)


@app.get("/gui2/{path:path}")
@app.get("/gui2")
def spa(path: str = "") -> FileResponse:
    """Serve the built gui2 SPA, falling back to index.html for client routes."""
    root = config.CLIENT_BUILD.resolve()
    candidate = (root / path).resolve()
    if path and candidate.is_file() and str(candidate).startswith(str(root)):
        return FileResponse(candidate)
    return FileResponse(root / "index.html")
