from __future__ import annotations

import json
import subprocess
from pathlib import Path

from coachme.benchmark.core.data.paths import read_json
from coachme.benchmark.core.run.runner import run_benchmark
from tests.benchmark.conftest import make_manifest


def _report(strategy: str) -> dict:
    report = {
        "date": "2026-10-20",
        "sport": "table tennis",
        "summary": "A clean report.",
        "strengths": [],
        "issues": [
            {
                "issue": "Late footwork at contact",
                "evidence_times": [2.0],
                "confidence": "medium",
            }
        ],
        "drills": [],
        "focus": "footwork",
        "progress": "",
        "limitations": [],
    }
    if strategy == "investigator":
        report.update(
            {
                "mode": "investigator",
                "evidence": ["ev_1"],
                "investigation": {
                    "coverage": {"vision": True},
                    "untested": [],
                    "stop_reason": "evidence_sufficient",
                    "timeline": [{"tool": "get_overview"}, {"tool": "look"}],
                    "budget": {"tool_calls": 2, "frames": 12, "tokens": 500, "seconds": 4.0},
                },
            }
        )
        report["issues"][0]["evidence_ids"] = ["ev_1"]
    return report


def test_runner_writes_raw_traces_and_blind_packets(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=2)
    out = tmp_path / "run"
    calls: list[str] = []

    def executor(clip: Path, strategy: str, analysis_root: Path) -> subprocess.CompletedProcess[str]:
        calls.append(strategy)
        analysis_root.mkdir(parents=True, exist_ok=True)
        (analysis_root / f"{clip.stem}_report.json").write_text(json.dumps(_report(strategy)), encoding="utf-8")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    run = run_benchmark(
        manifest_path=manifest,
        out=out,
        modes=["standard", "investigator"],
        required_clips=2,
        executor=executor,
    )
    assert run["status"] == "complete"
    assert len(calls) == 4
    assert (out / "raw" / "standard" / "clip-1.json").is_file()
    assert (out / "raw" / "investigator" / "clip-1.json").is_file()
    assert (out / "traces" / "investigator" / "clip-1.json").is_file()
    assert (out / "blind" / "clip-1" / "A.json").is_file()
    assert (out / "blind" / "clip-1" / "B.json").is_file()
    mapping = read_json(out / "mapping.json")
    assert set(mapping["clips"]["clip-1"].values()) >= {"standard", "investigator"}


def test_runner_resume_skips_existing_outputs(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    out = tmp_path / "run"

    def executor(clip: Path, strategy: str, analysis_root: Path) -> subprocess.CompletedProcess[str]:
        analysis_root.mkdir(parents=True, exist_ok=True)
        (analysis_root / f"{clip.stem}_report.json").write_text(json.dumps(_report(strategy)), encoding="utf-8")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    run_benchmark(
        manifest_path=manifest,
        out=out,
        modes=["standard"],
        required_clips=1,
        executor=executor,
    )

    def must_not_run(clip: Path, strategy: str, analysis_root: Path) -> subprocess.CompletedProcess[str]:
        raise AssertionError("resume should not call the executor for a complete clip")

    resumed = run_benchmark(
        manifest_path=manifest,
        out=out,
        modes=["standard"],
        required_clips=1,
        resume=True,
        executor=must_not_run,
    )
    assert resumed["status"] == "complete"


def test_runner_marks_negative_control(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path, count=1)
    out = tmp_path / "negative"

    def executor(clip: Path, strategy: str, analysis_root: Path) -> subprocess.CompletedProcess[str]:
        analysis_root.mkdir(parents=True, exist_ok=True)
        (analysis_root / f"{clip.stem}_report.json").write_text(json.dumps(_report(strategy)), encoding="utf-8")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    run = run_benchmark(
        manifest_path=manifest,
        out=out,
        modes=["standard"],
        required_clips=1,
        negative_control=True,
        executor=executor,
    )
    assert run["label"] == "negative-control"
    assert (out / ".negative-control").is_file()
    assert run["config"]["negative_control"] is True
