import sqlite3
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db

EXPECTED_TABLES = {
    "photos",
    "quests",
    "gpx_files",
    "gpx_trackpoints",
    "geocode_cache",
    "system_state",
    "schema_migrations",
    "deleted_photos",
}

EXPECTED_INDEXES = {
    "idx_photos_captured_at",
    "idx_photos_lat_lon",
    "idx_photos_quest",
    "idx_photos_orphan",
    "idx_photos_thumb_status",
    "idx_quests_started_at",
    "idx_trackpoints_gpx_file",
    "idx_trackpoints_recorded_at",
}


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row["name"] for row in rows}


def _index_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    return {row["name"] for row in rows}


def test_init_db_creates_all_tables() -> None:
    init_db()
    with get_connection() as conn:
        assert EXPECTED_TABLES.issubset(_table_names(conn))


def test_init_db_creates_all_indexes() -> None:
    init_db()
    with get_connection() as conn:
        assert EXPECTED_INDEXES.issubset(_index_names(conn))


def test_init_db_is_idempotent() -> None:
    init_db()
    init_db()
    with get_connection() as conn:
        assert EXPECTED_TABLES.issubset(_table_names(conn))


def test_migration_version_recorded() -> None:
    init_db()
    with get_connection() as conn:
        rows = conn.execute("SELECT version FROM schema_migrations").fetchall()
        versions = {row["version"] for row in rows}
    assert "001_init" in versions


def test_wal_mode_enabled() -> None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("PRAGMA journal_mode").fetchone()
    assert row[0] == "wal"


def test_foreign_keys_enabled() -> None:
    init_db()
    with get_connection() as conn:
        row = conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1
