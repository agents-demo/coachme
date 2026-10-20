"""Local-only FastAPI app for benchmark review and labelling.

Run it with ``coachme-benchmark ui``. The app binds to loopback by default and
serves the built SvelteKit client from ``ui/client/build`` when present.
"""

from __future__ import annotations

import asyncio
import io
import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse

from coachme.benchmark.manual_review import (
    import_hallucination_review,
    import_tool_review,
    write_hallucination_template,
    write_tool_template,
)
from coachme.benchmark.paths import BenchmarkError, data_root
from coachme.benchmark.ratings import import_rating_csv, rater_packet_zip
from coachme.benchmark.review import import_review, write_template
from coachme.benchmark.schemas import load_manifest
from coachme.benchmark.scorer import score_run
from coachme.benchmark.stability import compare_runs
from coachme.benchmark.ui.server import auth, ratings_api, read, run_control
from coachme.benchmark.ui.server.auth import current_root

CLIENT_BUILD = Path(__file__).resolve().parents[1] / "client" / "build"


def _error(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def create_app(root: str | Path | None = None) -> FastAPI:
    default_root = Path(root).expanduser().resolve() if root else data_root()
    auth_on = auth.enabled()
    app = FastAPI(title="CoachMe Benchmark", version="0.1.0")
    app.state.benchmark_root = default_root
    app.state.auth_enabled = auth_on
    if auth_on:
        auth.bootstrap_admin(default_root)

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path
        public_api = path in {"/api/health", "/api/auth/login"}
        public_ui = path in {"/login", "/favicon.ico", "/favicon.svg"} or path.startswith("/_app/")
        if not auth_on:
            token = auth.set_context(default_root, None)
            try:
                return await call_next(request)
            finally:
                auth.reset_context(token)
        user = auth.read_token(default_root, request.cookies.get(auth.COOKIE))
        if user is None:
            if public_api:
                token = auth.set_context(default_root, None)
                try:
                    return await call_next(request)
                finally:
                    auth.reset_context(token)
            if public_ui:
                token = auth.set_context(default_root, None)
                try:
                    return await call_next(request)
                finally:
                    auth.reset_context(token)
            if path.startswith("/api/"):
                return JSONResponse({"error": {"code": "unauthorized", "message": "login required"}}, status_code=401)
            return RedirectResponse("/login")
        if path.startswith("/api/") and not auth.allowed(str(user["role"]), request.method, path):
            return JSONResponse({"error": {"code": "forbidden", "message": "insufficient role"}}, status_code=403)
        try:
            root_for_user = auth.tenant_root(default_root, str(user.get("tenant") or "default"))
        except BenchmarkError as exc:
            return JSONResponse({"error": {"code": "tenant_error", "message": str(exc)}}, status_code=500)
        token = auth.set_context(root_for_user, user)
        try:
            return await call_next(request)
        finally:
            auth.reset_context(token)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5175", "http://127.0.0.1:5175"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def effective_rater(value: str) -> str:
        user = auth.current_user()
        if user and user.get("role") not in {"admin", "operator"}:
            return str(user["username"])
        return value

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "version": "0.1.0",
            "data_root": None if auth_on else str(default_root),
            "auth_enabled": auth_on,
            "active_run": None if auth_on else run_control.active_run(current_root()),
        }

    @app.post("/api/auth/login")
    def login(payload: dict[str, Any] = Body(...)) -> Response:  # noqa: B008
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "")
        user = auth.UserStore(default_root).authenticate(username, password)
        if user is None:
            raise HTTPException(status_code=401, detail=_error("unauthorized", "invalid username or password"))
        response = JSONResponse({"user": user})
        response.set_cookie(value=auth.issue_token(default_root, user), **auth.cookie_options())
        return response

    @app.get("/api/auth/me")
    def me() -> dict[str, Any]:
        user = auth.current_user()
        if user is None:
            raise HTTPException(status_code=401, detail=_error("unauthorized", "login required"))
        return {"user": user, "auth_enabled": app.state.auth_enabled}

    @app.post("/api/auth/logout")
    def logout() -> Response:
        response = JSONResponse({"ok": True})
        response.delete_cookie(auth.COOKIE)
        return response

    @app.get("/api/runs")
    def runs() -> dict[str, Any]:
        return {"runs": read.list_runs(current_root())}

    @app.get("/api/runs/active")
    def active_run() -> dict[str, Any]:
        return {"active": run_control.active_run(current_root())}

    @app.post("/api/runs", status_code=202)
    def create_run(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:  # noqa: B008
        try:
            return run_control.start_run(current_root(), payload)
        except run_control.InvalidRun as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_run", "run request failed validation", {"problems": exc.problems}),
            ) from exc
        except run_control.RunControlError as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc

    @app.post("/api/runs/import", status_code=201)
    def import_run(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:  # noqa: B008
        try:
            return run_control.import_run(
                current_root(),
                str(payload.get("path") or ""),
                confirm=bool(payload.get("confirm")),
            )
        except run_control.InvalidRun as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_run", "import failed validation", {"problems": exc.problems}),
            ) from exc
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}")
    def run_detail(run_id: str) -> dict[str, Any]:
        try:
            detail = read.run_detail(current_root(), run_id)
            active = run_control.active_run(current_root())
            detail["active"] = bool(active and active.get("run_id") == run_id)
            return detail
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.post("/api/runs/{run_id}/cancel")
    def cancel_run(run_id: str) -> dict[str, Any]:
        try:
            return run_control.cancel_run(current_root(), run_id)
        except run_control.RunControlError as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc

    @app.post("/api/runs/{run_id}/resume")
    def resume_run(run_id: str) -> dict[str, Any]:
        try:
            return run_control.resume_run(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except run_control.InvalidRun as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_run", "resume failed validation", {"problems": exc.problems}),
            ) from exc
        except run_control.RunControlError as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc

    @app.delete("/api/runs/{run_id}")
    def delete_run(run_id: str, confirm: str) -> dict[str, Any]:
        if confirm != run_id:
            raise HTTPException(status_code=400, detail=_error("confirmation_required", "confirm must equal run_id"))
        try:
            run_path = read.run_dir(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        active = run_control.active_run(current_root())
        if active and active.get("run_id") == run_id:
            raise HTTPException(status_code=409, detail=_error("conflict", "run is active"))
        shutil.rmtree(run_path)
        return {"deleted": run_id}

    @app.get("/api/runs/{run_id}/progress")
    def progress(run_id: str) -> dict[str, Any]:
        try:
            detail = read.run_detail(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        return {
            "run_id": run_id,
            "status": detail.get("status"),
            "clips_complete": detail.get("clips_complete", 0),
            "clips_total": detail.get("clips_total", 0),
            "score_status": detail.get("score_status"),
            "updated_at": detail.get("created_at"),
        }

    @app.get("/api/runs/{run_id}/stream")
    async def run_stream(run_id: str) -> StreamingResponse:
        try:
            read.run_dir(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

        async def events():
            while True:
                try:
                    detail = read.run_detail(current_root(), run_id)
                except read.NotFound:
                    yield f"data: {json.dumps({'error': 'run not found'})}\n\n"
                    return
                payload = {
                    "run_id": run_id,
                    "status": detail.get("status"),
                    "active": detail.get("active"),
                    "clips_complete": detail.get("clips_complete", 0),
                    "clips_total": detail.get("clips_total", 0),
                    "score_status": detail.get("score_status"),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                if payload["status"] in {"complete", "failed", "cancelled"} and not payload["active"]:
                    yield "event: close\ndata: {}\n\n"
                    return
                await asyncio.sleep(1.0)

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/runs/{run_id}/clips")
    def clips(run_id: str) -> dict[str, Any]:
        try:
            return {"clips": read.clip_summaries(current_root(), run_id)}
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}/clips/{clip_id}")
    def clip(run_id: str, clip_id: str) -> dict[str, Any]:
        try:
            return read.clip_detail(current_root(), run_id, clip_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}/rate")
    def rate_queue(run_id: str, rater: str = Query(...)) -> dict[str, Any]:
        try:
            return ratings_api.rate_queue(current_root(), run_id, effective_rater(rater))
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}/ratings/{rater}")
    def rating_sheet(run_id: str, rater: str) -> dict[str, Any]:
        try:
            return ratings_api.rating_sheet(current_root(), run_id, effective_rater(rater))
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.post("/api/runs/{run_id}/ratings/import")
    def import_ratings(
        run_id: str,
        rater: str = Form(...),
        file: UploadFile = File(...),  # noqa: B008
        force: bool = Form(False),
    ) -> dict[str, Any]:
        try:
            run_path = read.run_dir(current_root(), run_id)
            suffix = Path(file.filename or "ratings.csv").suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=run_path) as handle:
                shutil.copyfileobj(file.file, handle)
                temp_path = Path(handle.name)
            try:
                return import_rating_csv(run_dir=run_path, rater=rater, csv_path=temp_path, force=force)
            finally:
                temp_path.unlink(missing_ok=True)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=_error("invalid_csv", str(exc))) from exc

    @app.get("/api/runs/{run_id}/blind/{clip_id}")
    def blind(run_id: str, clip_id: str, rater: str = Query(...)) -> dict[str, Any]:
        try:
            return ratings_api.blind_packet(current_root(), run_id, clip_id, effective_rater(rater))
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingConflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc

    @app.put("/api/runs/{run_id}/ratings/{rater}/{clip_id}")
    def save_rating(
        run_id: str,
        rater: str,
        clip_id: str,
        payload: dict[str, Any] = Body(...),  # noqa: B008
        if_match: str | None = Header(default=None, alias="If-Match"),
    ) -> dict[str, Any]:
        if not if_match:
            raise HTTPException(status_code=428, detail=_error("precondition_required", "If-Match is required"))
        try:
            return ratings_api.save_rating(
                current_root(), run_id, effective_rater(rater), clip_id, payload, if_match=if_match
            )
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingConflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc
        except ratings_api.RatingInvalid as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_rating", "rating failed validation", {"problems": exc.problems}),
            ) from exc

    @app.post("/api/runs/{run_id}/ratings/{rater}/submit")
    def submit_ratings(run_id: str, rater: str) -> dict[str, Any]:
        try:
            return ratings_api.submit_ratings(current_root(), run_id, effective_rater(rater))
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingInvalid as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_rating", "rating failed validation", {"problems": exc.problems}),
            ) from exc

    @app.post("/api/runs/{run_id}/ratings/{rater}/{clip_id}/reopen")
    def reopen_rating(
        run_id: str,
        rater: str,
        clip_id: str,
        payload: dict[str, Any] = Body(...),  # noqa: B008
    ) -> dict[str, Any]:
        try:
            return ratings_api.reopen_rating(
                current_root(), run_id, effective_rater(rater), clip_id, reason=str(payload.get("reason", ""))
            )
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingConflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc
        except ratings_api.RatingInvalid as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_rating", "reopen failed validation", {"problems": exc.problems}),
            ) from exc

    @app.get("/api/runs/{run_id}/adjudication")
    def adjudication_queue(run_id: str) -> dict[str, Any]:
        try:
            return ratings_api.adjudication_queue(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}/adjudication/{clip_id}")
    def adjudication_detail(run_id: str, clip_id: str) -> dict[str, Any]:
        try:
            return ratings_api.adjudication_detail(current_root(), run_id, clip_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingConflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc

    @app.put("/api/runs/{run_id}/adjudication/{clip_id}")
    def save_adjudication(
        run_id: str,
        clip_id: str,
        payload: dict[str, Any] = Body(...),  # noqa: B008
        if_match: str | None = Header(default=None, alias="If-Match"),
    ) -> dict[str, Any]:
        if not if_match:
            raise HTTPException(status_code=428, detail=_error("precondition_required", "If-Match is required"))
        try:
            return ratings_api.save_adjudication(current_root(), run_id, clip_id, payload, if_match=if_match)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except ratings_api.RatingConflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc
        except ratings_api.RatingInvalid as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_rating", "adjudication failed validation", {"problems": exc.problems}),
            ) from exc

    @app.get("/api/runs/{run_id}/media/{clip_id}/source")
    def media(run_id: str, clip_id: str) -> FileResponse:
        try:
            path = read.source_path(current_root(), run_id, clip_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        return FileResponse(path, headers={"Cache-Control": "no-store, max-age=0"})

    @app.get("/api/runs/{run_id}/media/{clip_id}/artifact/{kind}")
    def artifact(run_id: str, clip_id: str, kind: str) -> FileResponse:
        try:
            path = read.artifact_path(current_root(), run_id, clip_id, kind)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        return FileResponse(path, headers={"Cache-Control": "no-store, max-age=0"})

    @app.get("/api/labels")
    def labels() -> dict[str, Any]:
        return read.labels_document(current_root())

    @app.get("/api/labels/{clip_id}")
    def label(clip_id: str) -> dict[str, Any]:
        try:
            return read.get_label(current_root(), clip_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.get("/api/runs/{run_id}/labels/{clip_id}")
    def label_context(run_id: str, clip_id: str) -> dict[str, Any]:
        try:
            return read.label_context(current_root(), run_id, clip_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc

    @app.put("/api/labels/{clip_id}")
    def save_label(
        clip_id: str,
        payload: dict[str, Any] = Body(...),  # noqa: B008 (FastAPI dependency idiom)
        if_match: str | None = Header(default=None, alias="If-Match"),
        labeler: str = Query(default="coach-a"),
    ) -> dict[str, Any]:
        if not if_match:
            raise HTTPException(status_code=428, detail=_error("precondition_required", "If-Match is required"))
        try:
            return read.save_label(current_root(), clip_id, payload, if_match=if_match, labeler=labeler)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except read.Conflict as exc:
            raise HTTPException(status_code=409, detail=_error("conflict", str(exc))) from exc
        except read.Invalid as exc:
            raise HTTPException(
                status_code=422,
                detail=_error("invalid_label", "label failed validation", {"problems": exc.problems}),
            ) from exc

    @app.post("/api/runs/{run_id}/score")
    def score(run_id: str) -> dict[str, Any]:
        try:
            run = read.run_detail(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        if run.get("status") not in {"complete", "failed"}:
            raise HTTPException(
                status_code=409,
                detail=_error("invalid_state", "analysis must be complete before scoring"),
            )
        try:
            return score_run(current_root() / "runs" / run_id)
        except Exception as exc:  # noqa: BLE001 - surface scorer failures to the operator
            raise HTTPException(status_code=500, detail=_error("score_failed", str(exc))) from exc

    @app.post("/api/runs/{run_id}/rater-packets")
    def rater_packets(
        run_id: str,
        payload: dict[str, Any] = Body(...),  # noqa: B008
    ) -> Response:
        try:
            run_path = read.run_dir(current_root(), run_id)
            data = rater_packet_zip(run_path, list(payload.get("raters") or []))
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=_error("invalid_packet", str(exc))) from exc
        return Response(
            data,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{run_id}-rater-packets.zip"'},
        )

    @app.post("/api/runs/{run_id}/stability")
    def stability(run_id: str, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:  # noqa: B008
        against = str(payload.get("against") or "").strip()
        if not against:
            raise HTTPException(status_code=422, detail=_error("invalid_stability", "against is required"))
        try:
            run_path = read.run_dir(current_root(), run_id)
            against_path = read.run_dir(current_root(), against)
            return compare_runs(run_path, against_path)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=_error("stability_failed", str(exc))) from exc

    @app.get("/api/runs/{run_id}/reviews/{kind}/template")
    def review_template(run_id: str, kind: str) -> Response:
        try:
            run_path = read.run_dir(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / f"{kind}.csv"
            try:
                if kind == "evidence":
                    write_template(run_path, target)
                elif kind == "tool":
                    write_tool_template(run_path, target)
                elif kind == "hallucination":
                    write_hallucination_template(run_path, target)
                else:
                    raise HTTPException(status_code=400, detail=_error("invalid_review", "unknown review kind"))
                data = target.read_bytes()
            except HTTPException:
                raise
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=422, detail=_error("review_failed", str(exc))) from exc
        return Response(
            data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{run_id}-{kind}-review.csv"'},
        )

    @app.post("/api/runs/{run_id}/reviews/{kind}/import")
    def review_import(
        run_id: str,
        kind: str,
        reviewer: str = Form(...),
        file: UploadFile = File(...),  # noqa: B008
    ) -> dict[str, Any]:
        try:
            run_path = read.run_dir(current_root(), run_id)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", dir=run_path) as handle:
                shutil.copyfileobj(file.file, handle)
                temp_path = Path(handle.name)
            try:
                if kind == "evidence":
                    return import_review(run_path, temp_path, reviewer=reviewer)
                if kind == "tool":
                    return import_tool_review(run_path, temp_path, reviewer=reviewer)
                if kind == "hallucination":
                    return import_hallucination_review(run_path, temp_path, reviewer=reviewer)
                raise HTTPException(status_code=400, detail=_error("invalid_review", "unknown review kind"))
            finally:
                temp_path.unlink(missing_ok=True)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        except HTTPException:
            raise
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=_error("review_failed", str(exc))) from exc

    @app.get("/api/runs/{run_id}/export/{name}")
    def export(run_id: str, name: str):
        try:
            run_path = read.run_dir(current_root(), run_id)
        except read.NotFound as exc:
            raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
        whitelist = {
            "score.json": run_path / "score.json",
            "report.md": run_path / "report.md",
            "rating_sheet.csv": run_path / "rating_sheet.csv",
            "runner.log": run_path / "runner.log",
        }
        if name == "labels.json":
            try:
                detail = read.run_detail(current_root(), run_id)
            except read.NotFound as exc:
                raise HTTPException(status_code=404, detail=_error("not_found", str(exc))) from exc
            path = Path(str(detail.get("labels_path") or ""))
            if not path.is_file():
                raise HTTPException(status_code=404, detail=_error("not_found", "labels not found"))
            return FileResponse(path, filename="labels.json", headers={"Cache-Control": "no-store"})
        if name == "run.zip":
            if not run_path.is_dir():
                raise HTTPException(status_code=404, detail=_error("not_found", "run not found"))
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(run_path.rglob("*")):
                    relative = path.relative_to(run_path)
                    if not path.is_file() or "analysis" in relative.parts:
                        continue
                    if relative.name in {"ui_runner.out", "ui_job.json"}:
                        continue
                    archive.write(path, relative.as_posix())
            return Response(
                buffer.getvalue(),
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="{run_id}.zip"'},
            )
        path = whitelist.get(name)
        if path is None:
            raise HTTPException(status_code=400, detail=_error("invalid_export", "unknown export"))
        if not path.is_file():
            raise HTTPException(status_code=404, detail=_error("not_found", "export not generated"))
        return FileResponse(path, headers={"Cache-Control": "no-store"})

    @app.get("/api/manifest/validate")
    def validate_manifest_endpoint(path: str) -> dict[str, Any]:
        candidate = Path(path).expanduser().resolve()
        try:
            candidate.relative_to(current_root())
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=_error("path_outside_root", "manifest must be inside the benchmark data root"),
            ) from exc
        if not candidate.is_file():
            raise HTTPException(status_code=404, detail=_error("not_found", "manifest not found"))
        manifest, problems = load_manifest(candidate)
        return {"ok": not problems, "problems": problems, "clips": len(manifest.get("clips") or [])}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        index_file = CLIENT_BUILD / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        return HTMLResponse(
            "<h1>CoachMe benchmark</h1>"
            "<p>The API is running, but the review UI has not been built.</p>"
            "<p>Run <code>npm install &amp;&amp; npm run build</code> in "
            "<code>coachme/benchmark/ui/client</code>.</p>"
        )

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail=_error("not_found", "unknown endpoint"))
        root = CLIENT_BUILD.resolve()
        candidate = (root / path).resolve()
        if path and candidate.is_file() and str(candidate).startswith(str(root)):
            return FileResponse(candidate)
        index_file = root / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail=_error("not_found", "client not built"))

    return app


app = create_app()


__all__ = ["CLIENT_BUILD", "create_app"]
