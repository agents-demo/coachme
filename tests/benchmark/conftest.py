from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest


def write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def make_manifest(root: Path, *, count: int = 1, media_type: str = "video") -> Path:
    clips_dir = root / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for index in range(count):
        clip_id = f"clip-{index + 1}"
        filename = f"{clip_id}.mp4" if media_type == "video" else f"{clip_id}.jpg"
        payload = f"fixture-{clip_id}".encode()
        (clips_dir / filename).write_bytes(payload)
        clips.append(
            {
                "id": clip_id,
                "path": filename,
                "media_type": media_type,
                "sport": "table tennis",
                "duration_s": 10.0 if media_type == "video" else 0,
                "capture": "side-on",
                "notes": "fixture",
                "split": "benchmark",
                "fps": 30,
                "resolution": [1920, 1080],
                "people": ["participant-1"],
                "source": "recorded-for-benchmark",
                "license": "internal-benchmark",
                "consent": {
                    "granted": True,
                    "scope": "internal benchmark + model API processing",
                    "by": "participant",
                    "date": "2026-01-01",
                    "expires": "2999-01-01",
                    "retention_days": 365,
                },
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return write_json(
        root / "manifest.json",
        {"version": 1, "fixture_root": "clips", "clips": clips},
    )


def labels_for(clip_ids: list[str], *, theme: str = "footwork") -> dict[str, Any]:
    return {
        "version": 1,
        "labelers": [{"name": "coach-a", "labeled_at": "2026-10-18"}],
        "adjudication": {"by": "coach-b", "date": "2026-10-18", "notes": ""},
        "clips": {
            clip_id: {
                "acceptable_limitations": [],
                "zero_finding_reason": "",
                "findings": [
                    {
                        "id": "f1",
                        "text": "Late footwork at contact",
                        "themes": [theme],
                        "evidence_times": [2.0],
                        "severity": "medium",
                        "required_evidence": ["vision"],
                    }
                ],
            }
            for clip_id in clip_ids
        },
    }


@pytest.fixture
def manifest(tmp_path: Path) -> Path:
    return make_manifest(tmp_path, count=1)
