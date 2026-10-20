from __future__ import annotations

import atexit
import hashlib
import shutil
import tempfile
from pathlib import Path

import uvicorn

from coachme.benchmark.core.data.paths import atomic_write_json
from coachme.benchmark.ui.server.app import create_app


def _seed(root: Path) -> None:
    clips = root / "clips"
    clips.mkdir(parents=True, exist_ok=True)
    media = clips / "clip-1.mp4"
    media.write_bytes(b"e2e-fixture")
    digest = hashlib.sha256(media.read_bytes()).hexdigest()
    manifest = {
        "version": 1,
        "fixture_root": "clips",
        "clips": [
            {
                "id": "clip-1",
                "path": "clip-1.mp4",
                "media_type": "video",
                "sport": "table tennis",
                "duration_s": 10,
                "capture": "side-on",
                "notes": "e2e",
                "split": "benchmark",
                "fps": 30,
                "resolution": [1920, 1080],
                "people": ["participant-1"],
                "source": "recorded-for-benchmark",
                "license": "internal-benchmark",
                "consent": {
                    "granted": True,
                    "scope": "internal benchmark",
                    "by": "participant",
                    "date": "2026-01-01",
                    "expires": "2999-01-01",
                    "retention_days": 3650,
                },
                "sha256": digest,
            }
        ],
    }
    atomic_write_json(root / "manifest.json", manifest)
    atomic_write_json(
        root / "labels.json",
        {
            "version": 1,
            "labelers": [{"name": "coach-a", "labeled_at": "2026-10-20"}],
            "clips": {
                "clip-1": {
                    "acceptable_limitations": [],
                    "zero_finding_reason": "",
                    "findings": [
                        {
                            "id": "f1",
                            "text": "Late footwork at contact",
                            "themes": ["footwork"],
                            "evidence_times": [2.0],
                            "severity": "medium",
                            "required_evidence": ["vision"],
                        }
                    ],
                }
            },
        },
    )
    run = root / "runs" / "run-1"
    atomic_write_json(
        run / "run.json",
        {
            "run_id": "run-1",
            "label": "e2e",
            "status": "complete",
            "created_at": "2026-10-20T10:00:00Z",
            "environment": "local",
            "modes": ["standard", "investigator"],
            "manifest_path": str(root / "manifest.json"),
            "labels_path": str(root / "labels.json"),
            "required_clips": 8,
            "required_raters": 2,
            "clips_total": 1,
            "clips_complete": 1,
            "clips_failed": 0,
            "clips": {"clip-1": {"standard": {"status": "complete"}, "investigator": {"status": "complete"}}},
        },
    )
    report = {
        "summary": "Late footwork at contact.",
        "issues": [
            {
                "issue": "Late footwork at contact",
                "evidence_times": [2.0],
                "evidence_ids": ["ev_1"],
                "confidence": "medium",
            }
        ],
        "limitations": [],
        "artifacts": {"pose": str(run / "artifacts" / "pose.jpg")},
    }
    (run / "artifacts").mkdir(parents=True, exist_ok=True)
    (run / "artifacts" / "pose.jpg").write_bytes(b"jpg")
    atomic_write_json(run / "raw" / "standard" / "clip-1.json", report)
    atomic_write_json(run / "raw" / "investigator" / "clip-1.json", report)
    atomic_write_json(
        run / "traces" / "investigator" / "clip-1.json",
        {
            "tool_sequence": ["get_overview", "look"],
            "evidence": [{"id": "ev_1", "tool": "look", "window": [1.8, 2.2], "confidence": "medium"}],
            "budget": {"tokens": 100, "seconds": 5},
            "status": "complete",
        },
    )
    atomic_write_json(
        run / "blind" / "clip-1" / "A.json", {"summary": "Late footwork at contact.", "issues": [], "limitations": []}
    )
    atomic_write_json(
        run / "blind" / "clip-1" / "B.json", {"summary": "Late footwork at contact.", "issues": [], "limitations": []}
    )
    atomic_write_json(
        run / "mapping.json",
        {
            "version": 1,
            "clips": {"clip-1": {"A": "standard", "B": "investigator"}},
            "raters": {
                "coach-a": {"clip-1": {"A": "standard", "B": "investigator"}},
                "coach-b": {"clip-1": {"A": "standard", "B": "investigator"}},
            },
        },
    )
    atomic_write_json(
        run / "ratings" / "coach-b.json",
        {
            "version": 1,
            "run_id": "run-1",
            "rater": "coach-b",
            "clips": {
                "clip-1": {
                    "A_specific": 4,
                    "A_supported": 4,
                    "A_complete": 4,
                    "A_honest": 4,
                    "A_use": "yes",
                    "B_specific": 4,
                    "B_supported": 4,
                    "B_complete": 4,
                    "B_honest": 4,
                    "B_use": "yes",
                    "preferred": "A",
                    "rationale": "A is clearer.",
                    "notes": "",
                    "mapping": {"A": "standard", "B": "investigator"},
                    "submitted": True,
                }
            },
        },
    )


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="coachme-benchmark-e2e-"))
    _seed(root)
    atexit.register(lambda: shutil.rmtree(root, ignore_errors=True))
    uvicorn.run(create_app(root), host="127.0.0.1", port=8765, log_level="warning")


if __name__ == "__main__":
    main()
