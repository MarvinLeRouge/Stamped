import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stamped.api.main import app
from stamped.core.config import settings
from stamped.core.db import get_db, init_db


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def client() -> TestClient:
    init_db()
    return TestClient(app)


def test_status_returns_200(client: TestClient) -> None:
    r = client.get("/api/status")
    assert r.status_code == 200


def test_status_shape(client: TestClient) -> None:
    r = client.get("/api/status")
    data = r.json()
    assert set(data.keys()) == {
        "photos_total",
        "thumbs_done",
        "thumbs_pending",
        "orphans",
        "gpx_files",
        "quests",
        "last_index_at",
    }


def test_status_defaults_to_zero(client: TestClient) -> None:
    r = client.get("/api/status")
    data = r.json()
    assert data["photos_total"] == 0
    assert data["thumbs_done"] == 0
    assert data["thumbs_pending"] == 0
    assert data["orphans"] == 0
    assert data["quests"] == 0
    assert data["gpx_files"] == 0
    assert data["last_index_at"] is None


def test_status_reflects_system_state(client: TestClient) -> None:
    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        from stamped.core.db import get_connection

        with get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)",
                ("photos_total", "42"),
            )
            conn.commit()
            yield conn

    app.dependency_overrides[get_db] = _override_db
    try:
        r = client.get("/api/status")
        assert r.json()["photos_total"] == 42
    finally:
        app.dependency_overrides.clear()
