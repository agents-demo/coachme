from __future__ import annotations

import io
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from coachme.benchmark.paths import atomic_write_json
from coachme.benchmark.ui.server.app import create_app
from tests.benchmark.conftest import labels_for, make_manifest


def _root(tmp_path: Path) -> Path:
    make_manifest(tmp_path, count=1)
    atomic_write_json(tmp_path / "labels.json", labels_for(["clip-1"]))
    run = tmp_path / "runs" / "run-1"
    atomic_write_json(
        run / "run.json",
        {
            "run_id": "run-1",
            "created_at": "2026-10-20T10:00:00Z",
            "environment": "local",
            "modes": ["standard", "investigator"],
            "status": "complete",
            "manifest_path": str(tmp_path / "manifest.json"),
            "labels_path": str(tmp_path / "labels.json"),
            "required_clips": 8,
            "required_raters": 2,
            "clips_total": 1,
            "clips_complete": 1,
            "clips_failed": 0,
            "clips": {"clip-1": {"standard": {"status": "complete"}, "investigator": {"status": "complete"}}},
        },
    )
    artifact = run / "artifacts" / "pose.jpg"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(b"jpg")
    report = {
        "summary": "Stable report.",
        "artifacts": {"pose": str(artifact)},
        "issues": [
            {
                "issue": "Late footwork at contact",
                "evidence_times": [2.0],
                "evidence_ids": ["ev_1"],
                "confidence": "medium",
            }
        ],
        "limitations": [],
    }
    atomic_write_json(run / "raw" / "standard" / "clip-1.json", report)
    atomic_write_json(run / "raw" / "investigator" / "clip-1.json", report)
    atomic_write_json(
        run / "traces" / "investigator" / "clip-1.json",
        {"tool_sequence": ["get_overview", "look"], "evidence": [{"id": "ev_1", "tool": "look", "window": [1.8, 2.2]}]},
    )
    atomic_write_json(run / "blind" / "clip-1" / "A.json", {"summary": "Standard", "issues": [], "limitations": []})
    atomic_write_json(run / "blind" / "clip-1" / "B.json", {"summary": "Investigator", "issues": [], "limitations": []})
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
    (run / "runner.log").write_text("log\n", encoding="utf-8")
    return tmp_path


def test_ui_read_endpoints(tmp_path: Path) -> None:
    client = TestClient(create_app(_root(tmp_path)))
    assert client.get("/api/health").json()["ok"] is True

    runs = client.get("/api/runs").json()["runs"]
    assert runs[0]["run_id"] == "run-1"
    assert runs[0]["score_status"] == "missing"

    detail = client.get("/api/runs/run-1").json()
    assert detail["status"] == "complete"
    assert detail["labels_complete"] is True

    clips = client.get("/api/runs/run-1/clips").json()["clips"]
    assert clips[0]["clip_id"] == "clip-1"
    assert clips[0]["label_status"] == "complete"

    clip = client.get("/api/runs/run-1/clips/clip-1").json()
    assert clip["has_source"] is True
    assert "standard" in clip["reports"]
    assert "investigator" in clip["reports"]

    label_context = client.get("/api/runs/run-1/labels/clip-1").json()
    assert label_context["clip_id"] == "clip-1"
    assert "reports" not in label_context
    assert label_context["media_url"].endswith("/source")

    media = client.get("/api/runs/run-1/media/clip-1/source")
    assert media.status_code == 200
    assert media.content == b"fixture-clip-1"
    artifact = client.get("/api/runs/run-1/media/clip-1/artifact/pose")
    assert artifact.status_code == 200
    assert artifact.content == b"jpg"
    assert client.get("/api/runs/run-1/media/clip-1/artifact/secret").status_code == 404
    assert client.get("/api/runs/run-1/media/..%2F..%2Fmanifest/source").status_code == 404


def test_label_api_etag_and_isolation(tmp_path: Path) -> None:
    root = _root(tmp_path)
    client = TestClient(create_app(root))

    current = client.get("/api/labels/clip-1").json()
    assert "reports" not in current
    etag = current["etag"]

    without = client.put("/api/labels/clip-1", json={"findings": []})
    assert without.status_code == 428

    label = labels_for(["clip-1"])["clips"]["clip-1"]
    label["findings"][0]["text"] = "Updated late footwork at contact"
    saved = client.put(
        "/api/labels/clip-1",
        json=label,
        headers={"If-Match": f'"{etag}"'},
    )
    assert saved.status_code == 200, saved.text
    new_etag = saved.json()["etag"]
    assert new_etag != etag

    stale = client.put(
        "/api/labels/clip-1",
        json=label,
        headers={"If-Match": f'"{etag}"'},
    )
    assert stale.status_code == 409

    invalid = client.put(
        "/api/labels/clip-1",
        json={"findings": [], "zero_finding_reason": ""},
        headers={"If-Match": f'"{new_etag}"'},
    )
    assert invalid.status_code == 422


def test_exports_and_manifest_validation(tmp_path: Path) -> None:
    root = _root(tmp_path)
    client = TestClient(create_app(root))
    assert client.get("/api/runs/run-1/export/runner.log").status_code == 200
    assert client.get("/api/runs/run-1/export/score.json").status_code == 404
    assert client.get("/api/runs/run-1/export/secret.txt").status_code == 400

    valid = client.get("/api/manifest/validate", params={"path": str(root / "manifest.json")})
    assert valid.status_code == 200
    assert valid.json()["ok"] is True

    outside = client.get("/api/manifest/validate", params={"path": str(tmp_path.parent / "x.json")})
    assert outside.status_code == 400


def _rating(preferred: str = "A") -> dict:
    return {
        "A_specific": 5,
        "A_supported": 5,
        "A_complete": 4,
        "A_honest": 5,
        "A_use": "yes",
        "B_specific": 4,
        "B_supported": 4,
        "B_complete": 4,
        "B_honest": 4,
        "B_use": "yes",
        "preferred": preferred,
        "rationale": "A is more specific.",
        "notes": "",
    }


def test_blind_rating_and_adjudication(tmp_path: Path) -> None:
    client = TestClient(create_app(_root(tmp_path)))

    queue = client.get("/api/runs/run-1/rate", params={"rater": "coach-a"}).json()
    assert queue["total"] == 1
    assert queue["clips"][0]["state"] == "not_started"

    blind = client.get("/api/runs/run-1/blind/clip-1", params={"rater": "coach-a"}).json()
    assert blind["mapping"] is None
    assert set(blind["reports"]) == {"A", "B"}

    without = client.put("/api/runs/run-1/ratings/coach-a/clip-1", json=_rating())
    assert without.status_code == 428

    sheet = client.get("/api/runs/run-1/ratings/coach-a").json()
    saved = client.put(
        "/api/runs/run-1/ratings/coach-a/clip-1",
        json=_rating(),
        headers={"If-Match": f'"{sheet["etag"]}"'},
    )
    assert saved.status_code == 200, saved.text

    submitted = client.post("/api/runs/run-1/ratings/coach-a/submit")
    assert submitted.status_code == 200
    assert submitted.json()["submitted"] == 1

    locked = client.put(
        "/api/runs/run-1/ratings/coach-a/clip-1",
        json=_rating(),
        headers={"If-Match": f'"{submitted.json()["etag"]}"'},
    )
    assert locked.status_code == 409

    queue = client.get("/api/runs/run-1/adjudication").json()
    assert queue["ready"] is False

    # Second rater, then the mapping is revealed for adjudication.
    sheet_b = client.get("/api/runs/run-1/ratings/coach-b").json()
    assert (
        client.put(
            "/api/runs/run-1/ratings/coach-b/clip-1",
            json=_rating(),
            headers={"If-Match": f'"{sheet_b["etag"]}"'},
        ).status_code
        == 200
    )
    assert client.post("/api/runs/run-1/ratings/coach-b/submit").status_code == 200

    queue = client.get("/api/runs/run-1/adjudication").json()
    assert queue["ready"] is True
    assert queue["clips"][0]["votes"][0]["preferred"] == "standard"

    detail = client.get("/api/runs/run-1/adjudication/clip-1").json()
    assert detail["mapping"]["A"] == "standard"
    assert "standard" in detail["reports"]
    assert "investigator" in detail["reports"]

    assert (
        client.put(
            "/api/runs/run-1/adjudication/clip-1",
            json={"preferred": "B", "rationale": "B is better."},
        ).status_code
        == 428
    )
    decided = client.put(
        "/api/runs/run-1/adjudication/clip-1",
        json={"preferred": "B", "rationale": "B is better."},
        headers={"If-Match": f'"{detail["etag"]}"'},
    )
    assert decided.status_code == 200, decided.text
    assert (tmp_path / "runs" / "run-1" / "rating_sheet.csv").is_file()

    reopened = client.post(
        "/api/runs/run-1/ratings/coach-a/clip-1/reopen",
        json={"reason": "changed my mind"},
    )
    assert reopened.status_code == 409


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid
        import threading

        self.event = threading.Event()

    def wait(self) -> int:
        self.event.wait(timeout=30)
        return 0


def test_run_control_create_conflict_and_import(tmp_path: Path, monkeypatch) -> None:
    from coachme.benchmark.ui.server import run_control

    root = _root(tmp_path)
    process = _FakeProcess(__import__("os").getpid())
    commands: list[list[str]] = []

    def fake_spawn(command, log_path):
        commands.append(command)
        return process

    monkeypatch.setattr(run_control, "_spawn", fake_spawn)
    client = TestClient(create_app(root))

    payload = {
        "manifest_path": str(root / "manifest.json"),
        "modes": ["standard", "investigator"],
        "environment": "local",
        "label": "pilot",
        "required_clips": 8,
        "required_raters": 2,
    }
    created = client.post("/api/runs", json=payload)
    assert created.status_code == 202, created.text
    run_id = created.json()["run_id"]
    assert commands and "--out" in commands[0]
    active = client.get("/api/runs/active").json()["active"]
    assert active["run_id"] == run_id

    conflict = client.post("/api/runs", json=payload)
    assert conflict.status_code == 409

    process.event.set()
    for _ in range(20):
        if client.get("/api/runs/active").json()["active"] is None:
            break
        __import__("time").sleep(0.02)

    run_dir = root / "runs" / "existing"
    atomic_write_json(run_dir / "run.json", {"run_id": "existing", "status": "complete"})
    imported = client.post("/api/runs/import", json={"path": str(run_dir), "confirm": True})
    assert imported.status_code == 201
    assert imported.json()["run_id"] == "existing"


def test_run_control_rejects_bad_manifest(tmp_path: Path, monkeypatch) -> None:

    client = TestClient(create_app(_root(tmp_path)))
    bad = client.post(
        "/api/runs",
        json={"manifest_path": str(tmp_path / "missing.json"), "modes": ["standard"]},
    )
    assert bad.status_code == 422
    assert "manifest not found" in bad.json()["detail"]["error"]["details"]["problems"][0]


def test_rater_packets_have_no_mapping(tmp_path: Path) -> None:
    client = TestClient(create_app(_root(tmp_path)))
    response = client.post(
        "/api/runs/run-1/rater-packets",
        json={"raters": ["coach-a", "coach-b"]},
    )
    assert response.status_code == 200, response.text
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert "coach-a/ratings.csv" in names
        assert "coach-b/clip-1/A.json" in names
        assert not any("mapping" in name for name in names)
        assert "clip_id,rater" in archive.read("coach-a/ratings.csv").decode("utf-8")


def test_rater_csv_import_and_delete_run(tmp_path: Path) -> None:
    from coachme.benchmark.ratings import RATER_HEADER

    root = _root(tmp_path)
    client = TestClient(create_app(root))
    row = {
        "clip_id": "clip-1",
        "rater": "coach-a",
        "A_specific": 5,
        "A_supported": 5,
        "A_complete": 4,
        "A_honest": 5,
        "A_use": "yes",
        "B_specific": 4,
        "B_supported": 4,
        "B_complete": 4,
        "B_honest": 4,
        "B_use": "yes",
        "preferred": "A",
        "rationale": "A is more specific.",
        "notes": "",
    }
    import csv as _csv
    import io as _io

    buffer = _io.StringIO()
    writer = _csv.DictWriter(buffer, fieldnames=RATER_HEADER, lineterminator="\n")
    writer.writeheader()
    writer.writerow(row)
    response = client.post(
        "/api/runs/run-1/ratings/import",
        data={"rater": "coach-a", "force": "false"},
        files={"file": ("ratings.csv", buffer.getvalue().encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["clips"]["clip-1"]["submitted"] is True

    assert client.delete("/api/runs/run-1", params={"confirm": "wrong"}).status_code == 400
    deleted = client.delete("/api/runs/run-1", params={"confirm": "run-1"})
    assert deleted.status_code == 200
    assert not (root / "runs" / "run-1").exists()
