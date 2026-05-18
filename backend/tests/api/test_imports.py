import sqlite3
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from stamped.api.imports import _jobs
from stamped.api.main import app
from stamped.core.config import settings
from stamped.core.db import get_connection, get_db, init_db
from tests.conftest import make_jpeg


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    _jobs.clear()


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    init_db()
    return TestClient(app)


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


# ── POST /api/import ──────────────────────────────────────────────────────────


def test_start_import_returns_202(client: TestClient, tmp_path: Path) -> None:
    r = client.post("/api/import", json={"path": str(tmp_path)})
    assert r.status_code == 202


def test_start_import_returns_job_id(client: TestClient, tmp_path: Path) -> None:
    r = client.post("/api/import", json={"path": str(tmp_path)})
    data = r.json()
    assert "job_id" in data
    assert data["status"] == "started"


def test_start_import_invalid_path_returns_400(client: TestClient) -> None:
    r = client.post("/api/import", json={"path": "/does/not/exist"})
    assert r.status_code == 400


# ── GET /api/import/{job_id} ──────────────────────────────────────────────────


def test_get_import_status_returns_job(client: TestClient, tmp_path: Path) -> None:
    r = client.post("/api/import", json={"path": str(tmp_path)})
    job_id = r.json()["job_id"]
    r2 = client.get(f"/api/import/{job_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["job_id"] == job_id
    assert "phase" in data
    assert "progress" in data


def test_get_import_status_unknown_id_returns_404(client: TestClient) -> None:
    r = client.get("/api/import/nonexistent-uuid")
    assert r.status_code == 404


def test_get_import_status_shape(client: TestClient, tmp_path: Path) -> None:
    r = client.post("/api/import", json={"path": str(tmp_path)})
    job_id = r.json()["job_id"]
    data = client.get(f"/api/import/{job_id}").json()
    assert set(data.keys()) == {
        "job_id",
        "status",
        "phase",
        "progress",
        "indexed",
        "total",
        "errors",
        "started_at",
        "finished_at",
    }


# ── POST /api/reindex ─────────────────────────────────────────────────────────


def test_reindex_without_confirm_returns_400(client: TestClient) -> None:
    r = client.post("/api/reindex", json={"confirm": False})
    assert r.status_code == 400


def test_reindex_with_confirm_clears_data(
    client: TestClient, tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    make_jpeg(tmp_path / "photo.jpg", lat=45.0, lon=6.0)
    from stamped.services.import_service import import_directory

    import_directory(tmp_path, db_conn)

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    try:
        r = client.post("/api/reindex", json={"confirm": True})
        assert r.status_code == 200
        assert r.json() == {"status": "cleared"}
        count = db_conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        assert count == 0
    finally:
        app.dependency_overrides.clear()


# ── Pipeline integration ──────────────────────────────────────────────────────


def test_pipeline_updates_system_state(tmp_path: Path) -> None:
    make_jpeg(tmp_path / "photo.jpg", lat=45.0, lon=6.0, dt_str="2024:07:14 10:00:00")

    with patch("stamped.api.imports.enrich_elevation"), TestClient(app) as c:
        r = c.post("/api/import", json={"path": str(tmp_path)})
        job_id = r.json()["job_id"]
        import time

        for _ in range(20):
            status = c.get(f"/api/import/{job_id}").json()["status"]
            if status != "running":
                break
            time.sleep(0.1)

    with get_connection() as conn:
        val = conn.execute("SELECT value FROM system_state WHERE key = 'photos_total'").fetchone()
    assert val is not None
    assert int(val[0]) >= 1
