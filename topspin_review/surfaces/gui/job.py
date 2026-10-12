"""Background analysis job: start the worker, poll its progress, page prelude.

The analysis runs in its own process (see :mod:`topspin_review.core.jobs.worker`).
In-process runs collided with Streamlit's module handling: the backend runner
spawns subprocesses, and Streamlit's script module caused the spawned child to
re-import the backend as a second copy, breaking pickling of message objects.
The worker streams progress to a JSON file that we poll here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

from topspin_review.integrations.storage import runtime
from topspin_review.surfaces.gui import nav, style


def start_worker(target: Path, *, agentic: bool, box) -> None:
    progress_file = runtime.DATA_DIR / f"_progress_{target.stem}.json"
    try:
        progress_file.unlink()
    except OSError:
        pass
    cmd = [sys.executable, "-m", "topspin_review.core.jobs.worker", str(target), "--progress", str(progress_file)]
    if agentic:
        cmd.append("--agentic")
    if box:
        cmd += ["--box", ",".join(str(x) for x in box)]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(runtime.PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.Popen(
        cmd, cwd=str(runtime.PROJECT_ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    st.session_state["job"] = {
        "proc": proc,
        "progress": str(progress_file),
        "stem": target.stem,
        "start": time.monotonic(),
    }


def poll_job() -> None:
    job = st.session_state.get("job")
    if not job:
        return
    snap: dict = {}
    try:
        snap = json.loads(Path(job["progress"]).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        snap = {}
    proc: subprocess.Popen = job["proc"]
    if proc.poll() is None:
        pct = min(max(float(snap.get("pct") or 0.0), 0.0), 100.0)
        elapsed = time.monotonic() - float(job.get("start", time.monotonic()))
        bar_col, stop_col = st.columns([6, 1], vertical_alignment="bottom")
        bar_col.progress(pct / 100.0, text=f"Analyzing… {snap.get('stage', 'starting')} ({int(pct)}%) · {elapsed:.0f}s")
        if stop_col.button("Stop", key="stop_analysis"):
            try:
                proc.kill()
            except Exception:
                pass
            st.session_state.pop("job", None)
            st.session_state["job_error"] = "Analysis stopped."
            st.rerun()
        time.sleep(0.5)
        st.rerun()
    st.session_state.pop("job", None)
    if snap.get("error"):
        st.session_state["job_error"] = snap["error"]
        st.rerun()
    st.session_state["latest_stem"] = snap.get("stem") or job.get("stem")
    nav.go("Result")


def prelude() -> None:
    """Runs at the top of every page: inject style, show errors, poll the job."""
    style.inject_style()
    if st.session_state.get("job_error"):
        st.error(f"Analysis failed: {st.session_state.pop('job_error')}")
    poll_job()
