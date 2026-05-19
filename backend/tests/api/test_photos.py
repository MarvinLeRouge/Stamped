import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stamped.api.main import app
from stamped.core.config import settings
from stamped.core.db import get_connection, get_db, init_db
from tests.conftest import make_jpeg


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


@pytest.fixture()
def client() -> TestClient:
    init_db()
    return TestClient(app)


def _insert_photo(
    conn: sqlite3.Connection,
    file_path: str = "photo.jpg",
    file_hash: str = "a" * 64,
    thumb_path: str | None = None,
    thumb_status: str = "pending",
) -> int:
    row = conn.execute(
        "INSERT INTO photos (file_path, file_hash, is_orphan, thumb_path, thumb_status)"
        " VALUES (?, ?, 0, ?, ?)",
        (file_path, file_hash, thumb_path, thumb_status),
    )
    conn.commit()
    return row.lastrowid  # type: ignore[return-value]


# ── GET /api/photos/{id}/thumb ────────────────────────────────────────────────


def test_get_thumb_returns_404_for_unknown_photo(client: TestClient) -> None:
    def _override() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override
    try:
        r = client.get("/api/photos/9999/thumb")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_thumb_returns_202_when_pending(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, thumb_status="pending")

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).get("/api/photos/1/thumb")
        assert r.status_code == 202
        assert r.headers["x-thumb-status"] == "pending"
    finally:
        app.dependency_overrides.clear()


def test_get_thumb_serves_file_when_done(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    jpeg = make_jpeg(tmp_path / "thumb.jpg")
    _insert_photo(db_conn, thumb_path=str(jpeg), thumb_status="done")

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).get("/api/photos/1/thumb")
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/jpeg"
    finally:
        app.dependency_overrides.clear()


# ── PATCH /api/photos/{id} ───────────────────────────────────────────────────


def test_patch_photo_unknown_returns_404(client: TestClient) -> None:
    def _override() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override
    try:
        r = client.patch("/api/photos/9999", json={"lat": 45.0, "lon": 6.0})
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_patch_photo_sets_coordinates(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn)

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).patch("/api/photos/1", json={"lat": 44.5, "lon": 6.3})
        assert r.status_code == 200
        assert r.json()["lat"] == pytest.approx(44.5)
        assert r.json()["lon"] == pytest.approx(6.3)
    finally:
        app.dependency_overrides.clear()


def test_patch_photo_clears_orphan_flag(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO photos (file_path, file_hash, is_orphan, thumb_status)"
        " VALUES ('p.jpg', 'hash-x', 1, 'pending')"
    )
    db_conn.commit()

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).patch("/api/photos/1", json={"lat": 44.5, "lon": 6.3})
        assert r.status_code == 200
        assert r.json()["is_orphan"] is False
    finally:
        app.dependency_overrides.clear()


def test_patch_photo_returns_full_summary_shape(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    _insert_photo(db_conn)

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).patch("/api/photos/1", json={"lat": 44.5, "lon": 6.3})
        assert set(r.json().keys()) == {
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


# ── POST /api/photos/{id}/thumb/priority ─────────────────────────────────────


def test_priority_thumb_returns_404_for_unknown(client: TestClient) -> None:
    def _override() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override
    try:
        r = client.post("/api/photos/9999/thumb/priority")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_priority_thumb_returns_queued(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, thumb_status="pending")

    def _override() -> Generator[sqlite3.Connection, None, None]:
        yield db_conn

    app.dependency_overrides[get_db] = _override
    try:
        r = TestClient(app).post("/api/photos/1/thumb/priority")
        assert r.status_code == 200
        assert r.json() == {"status": "queued"}
    finally:
        app.dependency_overrides.clear()
