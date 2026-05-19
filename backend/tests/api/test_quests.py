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


# ── GET /api/quests/{id}/trackpoints ─────────────────────────────────────────


def _trackpoints_client(tmp_path: Path) -> tuple[TestClient, int]:
    """Return a client with one quest and two GPX files (two segments)."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-01-01T00:00:00Z', '2024-01-01T02:00:00Z', 0, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'a.gpx', 'hash-a')",
            (quest_id,),
        )
        gpx1: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'b.gpx', 'hash-b')",
            (quest_id,),
        )
        gpx2: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.executemany(
            "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon) VALUES (?,?,?,?)",
            [
                (gpx1, "2024-01-01T08:00:00Z", 44.0, 6.0),
                (gpx1, "2024-01-01T08:10:00Z", 44.1, 6.1),
                (gpx2, "2024-01-01T10:00:00Z", 45.0, 7.0),
                (gpx2, "2024-01-01T10:10:00Z", 45.1, 7.1),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_get_trackpoints_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    c = TestClient(app)
    r = c.get("/api/quests/999/trackpoints")
    assert r.status_code == 404


def test_get_trackpoints_returns_two_segments(tmp_path: Path) -> None:
    c, quest_id = _trackpoints_client(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/trackpoints")
        assert r.status_code == 200
        segments = r.json()
        assert len(segments) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_trackpoints_segment_coordinates(tmp_path: Path) -> None:
    c, quest_id = _trackpoints_client(tmp_path)
    try:
        segments = c.get(f"/api/quests/{quest_id}/trackpoints").json()
        assert segments[0][0] == [44.0, 6.0]
        assert segments[0][1] == [44.1, 6.1]
        assert segments[1][0] == [45.0, 7.0]
        assert segments[1][1] == [45.1, 7.1]
    finally:
        app.dependency_overrides.clear()


def test_get_trackpoints_no_gpx_returns_empty(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.get(f"/api/quests/{quest_id}/trackpoints")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()
