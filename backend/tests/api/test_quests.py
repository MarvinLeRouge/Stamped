import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stamped.api.main import app
from stamped.core.config import settings
from stamped.core.db import get_connection, get_db, init_db


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def client() -> TestClient:
    init_db()
    return TestClient(app)


def _seeded_client(tmp_path: Path) -> TestClient:
    """Return a TestClient whose DB already has one quest."""
    init_db()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quests
                    (auto_name, started_at, ended_at, photo_count, has_gpx)
                VALUES ('Quest 2024-07-14', '2024-07-14T08:00:00Z', '2024-07-14T10:30:00Z', 3, 0)
                """
            )
            conn.commit()
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def test_get_quests_empty(client: TestClient) -> None:
    r = client.get("/api/quests")
    assert r.status_code == 200
    assert r.json() == []


def test_get_quests_returns_list(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        r = c.get("/api/quests")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


def test_get_quests_shape(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        r = c.get("/api/quests")
        quest = r.json()[0]
        assert set(quest.keys()) == {
            "id",
            "name",
            "auto_name",
            "started_at",
            "ended_at",
            "photo_count",
            "has_gpx",
            "bbox_lat_min",
            "bbox_lat_max",
            "bbox_lon_min",
            "bbox_lon_max",
        }
    finally:
        app.dependency_overrides.clear()


def test_get_quests_values(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest = c.get("/api/quests").json()[0]
        assert quest["auto_name"] == "Quest 2024-07-14"
        assert quest["started_at"] == "2024-07-14T08:00:00Z"
        assert quest["photo_count"] == 3
        assert quest["has_gpx"] is False
        assert quest["name"] is None
    finally:
        app.dependency_overrides.clear()
