"""Start, cancel and resume benchmark runs from the local UI."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.paths import PROJECT_ROOT, atomic_write_json, read_json
from coachme.benchmark.paths import run_id as new_run_id
from coachme.benchmark.schemas import MODES, load_manifest
from coachme.benchmark.ui.server import read

ENVIRONMENTS = {"local", "staging", "production"}


class RunControlError(RuntimeError):
    pass


class InvalidRun(RunControlError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("invalid run request")
        self.problems = problems


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _active_path(root: Path) -> Path:
    return root / "runs" / ".active.json"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def active_run(root: str | Path | None = None) -> dict[str, Any] | None:
    resolved = read.root_dir(root)
    data = read_json(_active_path(resolved), None)
    if not isinstance(data, dict):
        return None
    pid = data.get("pid")
    if not isinstance(pid, int) or not _pid_alive(pid):
        try:
            _active_path(resolved).unlink()
        except OSError:
            pass
        return None
    return data


def _clear_active(root: Path, run_id: str, pid: int) -> None:
    current = read_json(_active_path(root), {})
    if isinstance(current, dict) and current.get("run_id") == run_id and current.get("pid") == pid:
        try:
            _active_path(root).unlink()
        except OSError:
            pass


def _spawn(command: list[str], log_path: Path) -> subprocess.Popen:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("ab") as log:
        return subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )


def _wait_and_clear(root: Path, run_id: str, pid: int, process: subprocess.Popen) -> None:
    try:
        process.wait()
    finally:
        _clear_active(root, run_id, pid)


def _command(
    *,
    manifest: Path,
    run_dir: Path,
    modes: list[str],
    environment: str,
    label: str | None,
    required_clips: int,
    required_raters: int,
    resume: bool,
    negative_control: bool = False,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "coachme.benchmark.cli",
        "run",
        "--manifest",
        str(manifest),
        "--out",
        str(run_dir),
        "--modes",
        ",".join(modes),
        "--environment",
        environment,
        "--required-clips",
        str(required_clips),
        "--required-raters",
        str(required_raters),
    ]
    if label:
        command.extend(["--label", label])
    if resume:
        command.append("--resume")
    if negative_control:
        command.append("--negative-control")
    return command


def _validate_manifest(root: Path, manifest_path: str) -> tuple[Path, dict[str, Any]]:
    candidate = Path(manifest_path).expanduser().resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise InvalidRun(["manifest must be inside the benchmark data root"]) from exc
    if not candidate.is_file():
        raise InvalidRun([f"manifest not found: {candidate}"])
    manifest, problems = load_manifest(candidate)
    if problems:
        raise InvalidRun(problems)
    return candidate, manifest


def start_run(
    root: str | Path | None,
    payload: dict[str, Any],
    *,
    spawn: Any | None = None,
) -> dict[str, Any]:
    resolved = read.root_dir(root)
    if active_run(resolved):
        raise RunControlError("another benchmark run is already active")
    manifest_path, manifest = _validate_manifest(resolved, str(payload.get("manifest_path") or ""))
    modes = [str(item) for item in (payload.get("modes") or ["standard", "investigator"])]
    modes = list(dict.fromkeys(modes))
    unknown = sorted(set(modes) - set(MODES))
    if unknown or not modes:
        raise InvalidRun([f"unknown or empty modes: {', '.join(unknown) or 'none'}"])
    environment = str(payload.get("environment") or "local")
    if environment not in ENVIRONMENTS:
        raise InvalidRun(["environment must be local, staging or production"])
    required_clips = int(payload.get("required_clips") or 8)
    required_raters = int(payload.get("required_raters") or 2)
    if required_clips < 1 or required_raters < 1:
        raise InvalidRun(["required clips and raters must be positive"])
    label = str(payload.get("label") or "").strip() or None
    run_id = new_run_id()
    run_path = resolved / "runs" / run_id
    run_path.mkdir(parents=True, exist_ok=False)
    command = _command(
        manifest=manifest_path,
        run_dir=run_path,
        modes=modes,
        environment=environment,
        label=label,
        required_clips=required_clips,
        required_raters=required_raters,
        resume=False,
    )
    launcher = spawn or _spawn
    try:
        process = launcher(command, run_path / "ui_runner.out")
    except Exception as exc:  # noqa: BLE001
        raise RunControlError(f"could not start run: {exc}") from exc
    job = {
        "run_id": run_id,
        "pid": process.pid,
        "started_at": _now(),
        "command": command,
        "modes": modes,
        "environment": environment,
        "required_raters": required_raters,
    }
    atomic_write_json(run_path / "ui_job.json", job)
    atomic_write_json(_active_path(resolved), {"run_id": run_id, "pid": process.pid})
    threading.Thread(target=_wait_and_clear, args=(resolved, run_id, process.pid, process), daemon=True).start()
    if spawn is None:
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline and not (run_path / "run.json").is_file():
            time.sleep(0.1)
    return {"run_id": run_id, "status": "queued", "clips": len(manifest.get("clips") or [])}


def resume_run(
    root: str | Path | None,
    run_id: str,
    *,
    spawn: Any | None = None,
) -> dict[str, Any]:
    resolved = read.root_dir(root)
    if active_run(resolved):
        raise RunControlError("another benchmark run is already active")
    run_path = read.run_dir(resolved, run_id)
    run = read_json(run_path / "run.json", {})
    if not isinstance(run, dict) or not run:
        raise read.NotFound("run not found")
    if run.get("status") == "complete":
        raise RunControlError("run is already complete")
    manifest = Path(str(run.get("manifest_path") or ""))
    if not manifest.is_file():
        raise InvalidRun(["manifest not found"])
    modes = list(run.get("modes") or ["standard", "investigator"])
    command = _command(
        manifest=manifest,
        run_dir=run_path,
        modes=modes,
        environment=str(run.get("environment") or "local"),
        label=run.get("label"),
        required_clips=int(run.get("required_clips") or 8),
        required_raters=int(run.get("required_raters") or 2),
        resume=True,
        negative_control=(run_path / ".negative-control").is_file(),
    )
    launcher = spawn or _spawn
    process = launcher(command, run_path / "ui_runner.out")
    job = {
        "run_id": run_id,
        "pid": process.pid,
        "started_at": _now(),
        "command": command,
        "modes": modes,
        "environment": str(run.get("environment") or "local"),
        "required_raters": int(run.get("required_raters") or 2),
    }
    atomic_write_json(run_path / "ui_job.json", job)
    atomic_write_json(_active_path(resolved), {"run_id": run_id, "pid": process.pid})
    threading.Thread(target=_wait_and_clear, args=(resolved, run_id, process.pid, process), daemon=True).start()
    return {"run_id": run_id, "status": "resuming"}


def cancel_run(root: str | Path | None, run_id: str) -> dict[str, Any]:
    resolved = read.root_dir(root)
    current = active_run(resolved)
    if not current or current.get("run_id") != run_id:
        raise RunControlError("run is not active")
    pid = int(current["pid"])
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False,
                timeout=10,
            )
        else:
            os.kill(pid, signal.SIGTERM)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RunControlError(f"could not cancel run: {exc}") from exc
    run_path = resolved / "runs" / run_id
    run = read_json(run_path / "run.json", {})
    if isinstance(run, dict) and run:
        run["status"] = "cancelled"
        run["updated_at"] = _now()
        atomic_write_json(run_path / "run.json", run)
    _clear_active(resolved, run_id, pid)
    return {"run_id": run_id, "status": "cancelled"}


def import_run(root: str | Path | None, path: str, *, confirm: bool) -> dict[str, Any]:
    resolved = read.root_dir(root)
    if not confirm:
        raise InvalidRun(["import requires confirm=true"])
    candidate = Path(path).expanduser().resolve()
    try:
        candidate.relative_to(resolved / "runs")
    except ValueError as exc:
        raise InvalidRun(["run path must be inside the benchmark runs directory"]) from exc
    if not (candidate / "run.json").is_file():
        raise read.NotFound("run.json not found")
    return {"run_id": candidate.name, "status": "imported"}


__all__ = [
    "InvalidRun",
    "RunControlError",
    "active_run",
    "cancel_run",
    "import_run",
    "resume_run",
    "start_run",
]
