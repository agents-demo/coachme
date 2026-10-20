"""Run Standard, Guided and Investigator against a benchmark manifest."""

from __future__ import annotations

import logging
import os
import random
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachme.benchmark.paths import (
    PROJECT_ROOT,
    BenchmarkError,
    atomic_write_json,
    data_root,
    file_sha256_or_empty,
    read_json,
    sha256_file,
    sha256_json,
    sha256_text,
)
from coachme.benchmark.paths import (
    run_id as new_run_id,
)
from coachme.benchmark.schemas import MODES, clip_map, clip_path, load_manifest, normalize_report

LOGGER = logging.getLogger("coachme.benchmark")
PROMPT_FILES = {
    "standard": ["coachme/core/strategies/deterministic.py", "coachme/core/stages/coach/prompts.py"],
    "guided": ["coachme/core/strategies/agentic.py", "coachme/core/stages/coach/prompts.py"],
    "investigator": ["coachme/core/stages/investigate/prompts.py"],
}
TOOL_FILES = {
    "investigator": [
        "coachme/core/stages/investigate/tools.py",
        "coachme/core/stages/coach/report_tools.py",
    ]
}
DEFAULT_REQUIRED_CLIPS = 8
DEFAULT_REQUIRED_RATERS = 2

AnalysisExecutor = Callable[[Path, str, Path], subprocess.CompletedProcess[str]]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _code_revision() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def _models() -> dict[str, Any]:
    try:
        from coachme.integrations.agents import settings

        return {
            "provider": settings.model_provider(),
            "text": settings.text_model_name(),
            "vision": settings.vision_model_name(),
            "text_temperature": settings.text_temperature(),
            "vision_temperature": settings.vision_temperature(),
        }
    except Exception:  # noqa: BLE001 - benchmark metadata must not block a run
        return {"provider": "unknown"}


def _budgets() -> dict[str, Any]:
    from coachme.core import config

    return {
        "max_frames": config.max_frames(),
        "zoom_frames": config.zoom_frames(),
        "investigator_tool_calls": config.investigator_max_tool_calls(),
        "investigator_seconds": config.investigator_max_seconds(),
        "investigator_tokens": config.investigator_max_tokens(),
        "investigator_frames": config.investigator_max_frames(),
    }


def _file_hashes(paths: list[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in paths:
        path = PROJECT_ROOT / relative
        hashes[relative] = sha256_file(path) if path.is_file() else "missing"
    return hashes


def _version_hash(paths: list[str]) -> str:
    return sha256_json(_file_hashes(paths))


def config_snapshot(
    *,
    manifest_path: Path,
    labels_path: Path,
    modes: list[str],
) -> dict[str, Any]:
    prompt_files = {mode: _file_hashes(PROMPT_FILES[mode]) for mode in modes}
    tool_files = {mode: _file_hashes(TOOL_FILES[mode]) for mode in modes if mode in TOOL_FILES}
    prompt_versions = {mode: _version_hash(PROMPT_FILES[mode]) for mode in modes}
    tool_versions = {mode: _version_hash(TOOL_FILES[mode]) for mode in modes if mode in TOOL_FILES}
    return {
        "modes": modes,
        "strategy_map": {mode: MODES[mode] for mode in modes},
        "manifest_sha256": file_sha256_or_empty(manifest_path),
        "labels_sha256": file_sha256_or_empty(labels_path),
        "code_revision": _code_revision(),
        "prompt_versions": prompt_versions,
        "toolset_versions": tool_versions,
        "prompt_files": prompt_files,
        "toolset_files": tool_files,
        "models": _models(),
        "budgets": _budgets(),
    }


def config_hash(snapshot: dict[str, Any]) -> str:
    return sha256_json(snapshot)


def _write_run(run_dir: Path, run: dict[str, Any]) -> None:
    run["updated_at"] = _now()
    atomic_write_json(run_dir / "run.json", run)


def _setup_logger(run_dir: Path) -> logging.Logger:
    logger = logging.getLogger(f"coachme.benchmark.{run_dir.name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    handler = logging.FileHandler(run_dir / "runner.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger


def _default_executor(clip: Path, strategy: str, analysis_root: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COACHME_DATA_DIR"] = str(analysis_root)
    env["DEMO_FALLBACK"] = "false"
    if (analysis_root.parents[2] / ".negative-control").is_file():
        env["BENCHMARK_NEGATIVE_CONTROL"] = "1"
    env["VISION_CACHE"] = "false"
    env["PYTHONUNBUFFERED"] = "1"
    command = [
        sys.executable,
        "-m",
        "coachme.surfaces.cli",
        "analyze",
        str(clip),
        "--mode",
        strategy,
    ]
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _find_report(analysis_root: Path, clip: Path) -> dict[str, Any] | None:
    expected = analysis_root / f"{clip.stem}_report.json"
    if expected.is_file():
        report = read_json(expected)
        return report if isinstance(report, dict) and report else None
    for path in sorted(analysis_root.glob("*_report.json")):
        report = read_json(path)
        if isinstance(report, dict) and report:
            return report
    return None


def _investigation_artifact(report: dict[str, Any]) -> dict[str, Any]:
    path = (report.get("artifacts") or {}).get("investigation")
    if path:
        data = read_json(path)
        if isinstance(data, dict):
            return data
    return {}


def _trace(
    report: dict[str, Any],
    *,
    mode: str,
    clip_id: str,
    seconds: float,
) -> dict[str, Any]:
    investigation = report.get("investigation")
    investigation = investigation if isinstance(investigation, dict) else {}
    artifact = _investigation_artifact(report)
    evidence = artifact.get("evidence") if isinstance(artifact.get("evidence"), list) else []
    if not evidence and isinstance(investigation.get("timeline"), list):
        evidence = investigation["timeline"]
    evidence = [item for item in evidence if isinstance(item, dict)]

    tool_sequence: list[str] = []
    for item in evidence:
        tool = str(item.get("tool", "")).strip()
        if tool and (not tool_sequence or tool_sequence[-1] != tool):
            tool_sequence.append(tool)

    budget = investigation.get("budget")
    budget = budget if isinstance(budget, dict) else {}
    usage = report.get("usage") if isinstance(report.get("usage"), dict) else {}
    stop_reason = str(investigation.get("stop_reason") or "")
    status = "complete"
    if mode == "investigator" and stop_reason != "evidence_sufficient":
        status = "partial"
    if report.get("fallback"):
        status = "failed"

    return {
        "mode": mode,
        "clip_id": clip_id,
        "tool_sequence": tool_sequence if mode == "investigator" else [],
        "evidence": evidence if mode == "investigator" else [],
        "budget": {
            "tool_calls": int(budget.get("tool_calls", 0) or 0),
            "frames": int(budget.get("frames", report.get("frames", 0)) or 0),
            "tokens": int(budget.get("tokens", usage.get("total_tokens", 0)) or 0),
            "seconds": round(float(budget.get("seconds", seconds) or seconds), 2),
        },
        "status": status,
    }


def _blind_report(report: dict[str, Any]) -> dict[str, Any]:
    issues = []
    for issue in normalize_report(report, ""):
        issues.append(
            {
                "text": issue["text"],
                "themes": issue["themes"],
                "times": issue["times"],
                "confidence": issue["confidence"],
            }
        )
    return {
        "summary": str(report.get("summary", "")),
        "issues": issues,
        "limitations": [str(item) for item in (report.get("limitations") or [])],
    }


def write_blind_packets(run_dir: Path) -> None:
    """Create A/B packets when both Standard and Investigator reports exist."""
    raw_standard = run_dir / "raw" / "standard"
    raw_investigator = run_dir / "raw" / "investigator"
    if not raw_standard.is_dir() or not raw_investigator.is_dir():
        return
    mapping: dict[str, Any] = {"version": 1, "clips": {}, "raters": {}}
    for standard_path in sorted(raw_standard.glob("*.json")):
        clip_id = standard_path.stem
        investigator_path = raw_investigator / f"{clip_id}.json"
        if not investigator_path.is_file():
            continue
        standard = read_json(standard_path)
        investigator = read_json(investigator_path)
        if not isinstance(standard, dict) or not isinstance(investigator, dict):
            continue
        reports = {"standard": _blind_report(standard), "investigator": _blind_report(investigator)}
        seed = int(sha256_text(f"{run_dir.name}:{clip_id}")[:16], 16)
        names = ["standard", "investigator"]
        random.Random(seed).shuffle(names)
        for label, name in zip(("A", "B"), names, strict=True):
            atomic_write_json(run_dir / "blind" / clip_id / f"{label}.json", reports[name])
        mapping["clips"][clip_id] = {"seed": seed, "A": names[0], "B": names[1]}
    atomic_write_json(run_dir / "mapping.json", mapping)


def run_benchmark(
    *,
    manifest_path: str | Path,
    out: str | Path,
    modes: list[str],
    environment: str = "local",
    label: str | None = None,
    required_clips: int = DEFAULT_REQUIRED_CLIPS,
    required_raters: int = DEFAULT_REQUIRED_RATERS,
    resume: bool = False,
    fail_fast: bool = False,
    negative_control: bool = False,
    executor: AnalysisExecutor | None = None,
) -> dict[str, Any]:
    """Run the requested modes and write a complete run directory."""
    manifest_path = Path(manifest_path).expanduser().resolve()
    out = Path(out).expanduser().resolve()
    modes = list(dict.fromkeys(modes))
    unknown = sorted(set(modes) - set(MODES))
    if unknown:
        raise BenchmarkError(f"unknown benchmark mode(s): {', '.join(unknown)}")
    if not modes:
        raise BenchmarkError("at least one mode is required")
    if environment not in {"local", "staging", "production"}:
        raise BenchmarkError("environment must be local, staging or production")

    manifest, problems = load_manifest(manifest_path)
    if problems:
        raise BenchmarkError("invalid manifest:\n- " + "\n- ".join(problems))
    clips = clip_map(manifest)
    labels_path = manifest_path.parent / "labels.json"
    snapshot = config_snapshot(manifest_path=manifest_path, labels_path=labels_path, modes=modes)
    snapshot["negative_control"] = negative_control
    current_hash = config_hash(snapshot)

    out.mkdir(parents=True, exist_ok=True)
    if negative_control:
        (out / ".negative-control").write_text("1", encoding="utf-8")
        label = "negative-control"
    run_path = out / "run.json"
    existing = read_json(run_path, {})
    if existing and not resume:
        raise BenchmarkError(f"run already exists: {out}; use --resume or a new output directory")
    if existing and existing.get("config_hash") != current_hash:
        raise BenchmarkError("cannot resume: manifest, labels, models, budgets or code revision changed")

    run = (
        existing
        if isinstance(existing, dict) and existing
        else {
            "version": 1,
            "run_id": out.name or new_run_id(),
            "created_at": _now(),
            "label": label,
            "environment": environment,
            "modes": modes,
            "manifest_path": str(manifest_path),
            "labels_path": str(labels_path),
            "required_clips": required_clips,
            "required_raters": required_raters,
            "config_hash": current_hash,
            "config": snapshot,
            "status": "running",
            "clips": {},
        }
    )
    run["required_clips"] = required_clips
    run["required_raters"] = required_raters
    run["environment"] = environment
    run["modes"] = modes
    run["status"] = "running"
    _write_run(out, run)
    logger = _setup_logger(out)
    logger.info("run %s modes=%s clips=%s", out.name, modes, len(clips))

    executor = executor or _default_executor
    failures = 0
    for clip_id, clip in clips.items():
        run["clips"].setdefault(clip_id, {})
        try:
            source = clip_path(manifest, clip, manifest_path)
        except BenchmarkError as exc:
            for mode in modes:
                run["clips"][clip_id][mode] = {"status": "failed", "error": str(exc)}
            failures += 1
            continue
        for mode in modes:
            mode_state = run["clips"][clip_id].get(mode, {})
            raw_path = out / "raw" / mode / f"{clip_id}.json"
            if resume and raw_path.is_file() and mode_state.get("status") in {"complete", "partial"}:
                logger.info("resume: skip %s %s", clip_id, mode)
                continue
            strategy = MODES[mode]
            analysis_root = out / "analysis" / mode / clip_id
            shutil.rmtree(analysis_root, ignore_errors=True)
            analysis_root.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            logger.info("analyze %s %s (%s)", clip_id, mode, strategy)
            try:
                result = executor(source, strategy, analysis_root)
                seconds = time.monotonic() - started
                report = _find_report(analysis_root, source) if result.returncode == 0 else None
                if result.returncode != 0:
                    error = (result.stderr or result.stdout or "analysis failed").strip()[-2000:]
                    run["clips"][clip_id][mode] = {
                        "status": "failed",
                        "seconds": round(seconds, 2),
                        "error": error,
                    }
                    logger.error("failed %s %s: %s", clip_id, mode, error.splitlines()[-1])
                    failures += 1
                elif report is None:
                    run["clips"][clip_id][mode] = {
                        "status": "failed",
                        "seconds": round(seconds, 2),
                        "error": "no parsable report",
                    }
                    logger.error("failed %s %s: no parsable report", clip_id, mode)
                    failures += 1
                else:
                    atomic_write_json(raw_path, report)
                    trace = _trace(report, mode=mode, clip_id=clip_id, seconds=seconds)
                    atomic_write_json(out / "traces" / mode / f"{clip_id}.json", trace)
                    status = trace["status"] if trace["status"] != "failed" else "failed"
                    run["clips"][clip_id][mode] = {
                        "status": status,
                        "seconds": round(seconds, 2),
                        "report": str(raw_path.relative_to(out)),
                    }
                    if status == "failed":
                        failures += 1
                    logger.info("done %s %s status=%s %.1fs", clip_id, mode, status, seconds)
            except Exception as exc:  # noqa: BLE001 - isolate clip failures
                seconds = time.monotonic() - started
                run["clips"][clip_id][mode] = {
                    "status": "failed",
                    "seconds": round(seconds, 2),
                    "error": str(exc),
                }
                failures += 1
                logger.exception("failed %s %s", clip_id, mode)
            _write_run(out, run)
            if failures and fail_fast:
                break
        if failures and fail_fast:
            break

    write_blind_packets(out)
    run["status"] = "failed" if failures else "complete"
    run["score_status"] = "missing"
    run["clips_complete"] = sum(
        1
        for clip_state in run["clips"].values()
        if all(clip_state.get(mode, {}).get("status") == "complete" for mode in modes)
    )
    run["clips_total"] = len(clips)
    run["clips_failed"] = failures
    _write_run(out, run)
    logger.info("run %s finished status=%s failures=%s", out.name, run["status"], failures)
    return run


def default_run_dir(root: str | Path | None = None) -> Path:
    return data_root(root) / "runs" / new_run_id()


__all__ = [
    "DEFAULT_REQUIRED_CLIPS",
    "DEFAULT_REQUIRED_RATERS",
    "config_hash",
    "config_snapshot",
    "default_run_dir",
    "run_benchmark",
    "write_blind_packets",
]
