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
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


def _override(conn: sqlite3.Connection):  # type: ignore[no-untyped-def]
    def _dep() -> Generator[sqlite3.Connection, None, None]:
        yield conn

    return _dep


def _insert_photo(
    conn: sqlite3.Connection,
    lat: float | None = 45.0,
    lon: float | None = 6.0,
    captured_at: str = "2024-07-14T08:00:00Z",
    quest_id: int | None = None,
    is_orphan: int = 0,
    idx: int = 0,
) -> int:
    row = conn.execute(
        "INSERT INTO photos (file_path, file_hash, lat, lon, captured_at, is_orphan, quest_id)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        (f"p{idx}.jpg", f"h{idx}", lat, lon, captured_at, is_orphan, quest_id),
    )
    conn.commit()
    return row.lastrowid  # type: ignore[return-value]


def test_list_photos_empty(db_conn: sqlite3.Connection) -> None:
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


def test_list_photos_returns_all(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, idx=0)
    _insert_photo(db_conn, idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos")
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_photos_bbox_filter(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, lat=45.0, lon=6.0, idx=0)
    _insert_photo(db_conn, lat=48.0, lon=2.0, idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?lat_min=44&lat_max=46&lon_min=5&lon_max=7")
        data = r.json()
        assert len(data) == 1
        assert data[0]["lat"] == pytest.approx(45.0)
    finally:
        app.dependency_overrides.clear()


def test_list_photos_date_filter(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, captured_at="2024-01-01T00:00:00Z", idx=0)
    _insert_photo(db_conn, captured_at="2024-12-31T00:00:00Z", idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?date_from=2024-06-01T00:00:00Z")
        data = r.json()
        assert len(data) == 1
        assert "12-31" in data[0]["captured_at"]
    finally:
        app.dependency_overrides.clear()


def test_list_photos_date_to_filter(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, captured_at="2024-01-01T00:00:00Z", idx=0)
    _insert_photo(db_conn, captured_at="2024-12-31T00:00:00Z", idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?date_to=2024-06-01T00:00:00Z")
        data = r.json()
        assert len(data) == 1
        assert "01-01" in data[0]["captured_at"]
    finally:
        app.dependency_overrides.clear()


def test_list_photos_quest_filter(db_conn: sqlite3.Connection) -> None:
    conn = db_conn
    conn.execute(
        "INSERT INTO quests (auto_name, started_at, ended_at, photo_count)"
        " VALUES ('Q1','2024-01-01T00:00:00Z','2024-01-01T12:00:00Z',1)"
    )
    conn.commit()
    _insert_photo(conn, quest_id=1, idx=0)
    _insert_photo(conn, quest_id=None, idx=1)
    app.dependency_overrides[get_db] = _override(conn)
    try:
        r = TestClient(app).get("/api/photos?quest_id=1")
        assert len(r.json()) == 1
    finally:
        app.dependency_overrides.clear()


def test_list_photos_orphan_filter(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, is_orphan=1, lat=None, lon=None, idx=0)
    _insert_photo(db_conn, is_orphan=0, idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?orphan=true")
        assert len(r.json()) == 1
        assert r.json()[0]["is_orphan"] is True
    finally:
        app.dependency_overrides.clear()


def test_list_photos_limit_offset(db_conn: sqlite3.Connection) -> None:
    for i in range(5):
        _insert_photo(db_conn, idx=i)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?limit=2&offset=1")
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_list_photos_response_shape(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        photo = TestClient(app).get("/api/photos").json()[0]
        assert set(photo.keys()) == {
            "id",
            "lat",
            "lon",
            "captured_at",
            "thumb_status",
            "quest_id",
            "is_orphan",
        }
    finally:
        app.dependency_overrides.clear()


def test_list_photos_no_quest_filter(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
        " VALUES ('Q', '2024-01-01T00:00:00Z', '2024-01-01T01:00:00Z', 1, 0)"
    )
    db_conn.commit()
    _insert_photo(db_conn, quest_id=None, idx=0)
    _insert_photo(db_conn, quest_id=1, idx=1)
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/photos?no_quest=true")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["quest_id"] is None
    finally:
        app.dependency_overrides.clear()
