"""In-process job manager for gui2: run an analysis in a background thread.

Progress is reported through the pipeline's own :class:`~topspin_review.core.progress.Progress`,
so the SPA can show the same per-stage feed the CLI prints. Unlike the Streamlit GUI (which
spawns :mod:`topspin_review.core.jobs.worker` to avoid Streamlit's module handling), a plain
FastAPI process can run the analysis in a worker thread directly.
"""

from __future__ import annotations

import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from typing import Any

from topspin_review.core import Params, resolve
from topspin_review.core.bootstrap import run as run_async
from topspin_review.core.progress import Progress


@dataclass
class Job:
    id: str
    video_path: str
    region_box: tuple[float, float, float, float] | None
    agentic: bool
    language: str = "en"
    mode: str | None = None
    """Explicit strategy name (``deterministic``, ``agentic``, ``investigator``).
    When set it takes precedence over the ``agentic`` flag."""
    status: str = "queued"  # queued | running | done | failed | cancelled
    error: str = ""
    stem: str = ""
    started: float = field(default_factory=time.time)
    cancel_event: threading.Event = field(default_factory=threading.Event)
    """Set this event to request cooperative cancellation of the running analysis."""

    def snapshot(self, progress: Progress) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "video_path": self.video_path,
            "stem": self.stem,
            "mode": self.mode,
            "error": self.error,
            "progress": progress.snapshot(),
        }


class JobManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}
        self._progress: dict[str, Progress] = {}

    def submit(
        self,
        video_path: str,
        region_box=None,
        agentic: bool = False,
        language: str = "en",
        mode: str | None = None,
    ) -> str:
        job_id = uuid.uuid4().hex[:12]
        job = Job(
            id=job_id,
            video_path=video_path,
            region_box=region_box,
            agentic=agentic,
            language=language,
            mode=mode,
        )
        prog = Progress()
        with self._lock:
            self._jobs[job_id] = job
            self._progress[job_id] = prog
        threading.Thread(target=self._run, args=(job, prog), daemon=True).start()
        return job_id

    def _run(self, job: Job, prog: Progress) -> None:
        with self._lock:
            job.status = "running"
        try:
            from topspin_review.core import get_strategy

            if job.mode:
                strategy = get_strategy(job.mode)
            else:
                strategy = resolve(job.agentic)
            run_async(
                strategy.analyze(
                    Params(
                        video_path=job.video_path,
                        region_box=job.region_box,
                        progress=prog,
                        language=job.language,
                        cancel_event=job.cancel_event,
                    )
                )
            )
            job.stem = job.video_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].rsplit(".", 1)[0]
            prog.finish(job.stem)
            # Let the cancel_event be the authority — not the pre-set status field.
            with self._lock:
                job.status = "cancelled" if job.cancel_event.is_set() else "done"
        except Exception as exc:  # noqa: BLE001
            job.error = f"{exc}\n\n{traceback.format_exc()}"
            prog.fail(str(exc))
            with self._lock:
                job.status = "failed"

    def status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            prog = self._progress.get(job_id)
        if job is None or prog is None:
            return {"id": job_id, "status": "unknown"}
        return job.snapshot(prog)

    def jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            return [job.snapshot(self._progress[job.id]) for job in self._jobs.values()]

    def cancel(self, job_id: str) -> bool:
        """Signal cooperative cancellation.

        The job status transitions to ``"cancelling"`` immediately (for the UI)
        and to ``"cancelled"`` once the background thread confirms the stop.
        """
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None or job.status not in ("queued", "running"):
            return False
        job.cancel_event.set()
        job.status = "cancelling"  # intermediate — thread will write "cancelled"
        return True

    def retry(self, job_id: str) -> str | None:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            return None
        return self.submit(job.video_path, job.region_box, job.agentic, job.language, job.mode)


_MANAGER = JobManager()


def get_manager() -> JobManager:
    return _MANAGER
