from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from coachme.benchmark.core.data.paths import atomic_write_json
from coachme.benchmark.ui.server.app import create_app
from coachme.benchmark.ui.server.auth import UserStore
from tests.benchmark.conftest import make_manifest


def test_auth_required_roles_and_tenant_isolation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COACHME_BENCHMARK_AUTH", "1")
    root = tmp_path
    store = UserStore(root)
    store.add("admin", "secret-pass", role="admin", tenant="default")
    store.add("rater-a", "secret-pass", role="rater", tenant="tenant-b")
    tenant = root / "tenants" / "default"
    make_manifest(tenant, count=1)
    atomic_write_json(
        tenant / "runs" / "run-1" / "run.json",
        {
            "run_id": "run-1",
            "status": "complete",
            "manifest_path": str(tenant / "manifest.json"),
            "labels_path": str(tenant / "labels.json"),
            "clips": {"clip-1": {"standard": {"status": "complete"}}},
        },
    )

    client = TestClient(create_app(root))
    assert client.get("/api/runs").status_code == 401
    assert client.post("/api/auth/login", json={"username": "admin", "password": "bad"}).status_code == 401

    login = client.post("/api/auth/login", json={"username": "admin", "password": "secret-pass"})
    assert login.status_code == 200, login.text
    me = client.get("/api/auth/me").json()["user"]
    assert me["role"] == "admin"
    assert me["tenant"] == "default"
    assert len(client.get("/api/runs").json()["runs"]) == 1

    other = TestClient(create_app(root))
    assert other.post("/api/auth/login", json={"username": "rater-a", "password": "secret-pass"}).status_code == 200
    assert other.get("/api/runs").json()["runs"] == []
    assert other.get("/api/labels/clip-1").status_code == 403
    assert other.get("/api/runs/run-1/clips/clip-1").status_code == 403

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert client.get("/api/runs").status_code == 401
