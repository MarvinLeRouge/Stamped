import sqlite3
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.elevation_service import ElevationResult, enrich_elevation


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


def _insert_photo(
    conn: sqlite3.Connection,
    lat: float | None,
    lon: float | None,
    alt: float | None = None,
    idx: int = 0,
) -> int:
    row = conn.execute(
        "INSERT INTO photos (file_path, file_hash, is_orphan, lat, lon, alt)"
        " VALUES (?, ?, 0, ?, ?, ?)",
        (f"p{idx}.jpg", f"h{idx}", lat, lon, alt),
    )
    conn.commit()
    return row.lastrowid  # type: ignore[return-value]


def test_enrich_elevation_no_photos(db_conn: sqlite3.Connection) -> None:
    result = enrich_elevation(db_conn)
    assert result == ElevationResult(enriched=0, failed=0)


def test_enrich_elevation_skips_photos_without_gps(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, lat=None, lon=None)
    result = enrich_elevation(db_conn)
    assert result == ElevationResult(enriched=0, failed=0)


def test_enrich_elevation_skips_photos_with_existing_alt(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_photo(db_conn, lat=45.0, lon=6.0, alt=1200.0)
    result = enrich_elevation(db_conn)
    assert result == ElevationResult(enriched=0, failed=0)


def test_enrich_elevation_writes_alt_on_success(db_conn: sqlite3.Connection) -> None:
    pid = _insert_photo(db_conn, lat=45.0, lon=6.0)
    with patch("stamped.services.elevation_service.fetch_elevation", return_value=[1234.5]):
        result = enrich_elevation(db_conn)
    assert result.enriched == 1
    assert result.failed == 0
    row = db_conn.execute("SELECT alt, alt_src FROM photos WHERE id = ?", (pid,)).fetchone()
    assert row["alt"] == pytest.approx(1234.5)
    assert row["alt_src"] == "api"


def test_enrich_elevation_sets_none_src_on_failure(db_conn: sqlite3.Connection) -> None:
    pid = _insert_photo(db_conn, lat=45.0, lon=6.0)
    with patch("stamped.services.elevation_service.fetch_elevation", return_value=[None]):
        result = enrich_elevation(db_conn)
    assert result.enriched == 0
    assert result.failed == 1
    row = db_conn.execute("SELECT alt, alt_src FROM photos WHERE id = ?", (pid,)).fetchone()
    assert row["alt"] is None
    assert row["alt_src"] == "none"


def test_enrich_elevation_mixed_results(db_conn: sqlite3.Connection) -> None:
    pid1 = _insert_photo(db_conn, lat=45.0, lon=6.0, idx=0)
    pid2 = _insert_photo(db_conn, lat=46.0, lon=7.0, idx=1)
    with patch("stamped.services.elevation_service.fetch_elevation", return_value=[500.0, None]):
        result = enrich_elevation(db_conn)
    assert result.enriched == 1
    assert result.failed == 1
    r1 = db_conn.execute("SELECT alt_src FROM photos WHERE id = ?", (pid1,)).fetchone()
    r2 = db_conn.execute("SELECT alt_src FROM photos WHERE id = ?", (pid2,)).fetchone()
    assert r1["alt_src"] == "api"
    assert r2["alt_src"] == "none"
