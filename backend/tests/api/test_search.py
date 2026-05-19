import sqlite3
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

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


def _make_location(display_name: str, lat: float, lon: float) -> object:
    class FakeLocation:
        address = display_name
        latitude = lat
        longitude = lon
        raw = {"boundingbox": ["44.0", "46.0", "5.0", "7.0"]}

    return FakeLocation()


def test_geocode_returns_results(db_conn: sqlite3.Connection) -> None:
    from stamped.api.search import GeocodeResult

    fake = GeocodeResult(
        display_name="Chamonix, France",
        lat=45.923,
        lon=6.869,
        bbox_lat_min=44.0,
        bbox_lat_max=46.0,
        bbox_lon_min=5.0,
        bbox_lon_max=7.0,
    )
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        with patch("stamped.api.search._fetch_nominatim", return_value=[fake]):
            r = TestClient(app).get("/api/search/geocode?q=Chamonix")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["display_name"] == "Chamonix, France"
        assert data[0]["lat"] == pytest.approx(45.923)
    finally:
        app.dependency_overrides.clear()


def test_geocode_query_too_short(db_conn: sqlite3.Connection) -> None:
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        r = TestClient(app).get("/api/search/geocode?q=a")
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_geocode_returns_empty_on_no_results(db_conn: sqlite3.Connection) -> None:
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        with patch("stamped.api.search._fetch_nominatim", return_value=[]):
            r = TestClient(app).get("/api/search/geocode?q=xyzxyzxyz")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


def test_geocode_uses_cache(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO geocode_cache (lat_rounded, lon_rounded, place_name) VALUES (?, ?, ?)",
        (45.923, 6.869, "Chamonix, France"),
    )
    db_conn.commit()
    app.dependency_overrides[get_db] = _override(db_conn)
    try:
        with patch("stamped.api.search._fetch_nominatim") as mock_fetch:
            r = TestClient(app).get("/api/search/geocode?q=Chamonix")
        mock_fetch.assert_not_called()
        assert r.status_code == 200
    finally:
        app.dependency_overrides.clear()
