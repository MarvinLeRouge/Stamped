import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.import_service import (
    compute_hash,
    import_directory,
    scan_jpegs,
)
from tests.conftest import make_jpeg


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


def test_scan_jpegs_finds_all_jpeg_files(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    make_jpeg(tmp_path / "a.jpg")
    make_jpeg(sub / "b.JPG")
    (tmp_path / "note.txt").write_text("ignore")
    results = scan_jpegs(tmp_path)
    assert len(results) == 2


def test_compute_hash_is_deterministic(tmp_path: Path) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    assert compute_hash(jpeg) == compute_hash(jpeg)


def test_compute_hash_differs_for_different_files(tmp_path: Path) -> None:
    a = make_jpeg(tmp_path / "a.jpg", lat=45.0, lon=6.0)
    b = make_jpeg(tmp_path / "b.jpg", lat=48.0, lon=2.0)
    assert compute_hash(a) != compute_hash(b)


def test_import_directory_indexes_new_photos(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    make_jpeg(tmp_path / "a.jpg", lat=45.832, lon=6.865, dt_str="2024:07:14 10:00:00")
    make_jpeg(tmp_path / "b.jpg", lat=48.858, lon=2.294, dt_str="2024:07:14 18:00:00")
    result = import_directory(tmp_path, db_conn)
    assert result.indexed == 2
    assert result.skipped == 0
    assert result.errors == 0


def test_import_directory_skips_duplicate_hash(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    make_jpeg(tmp_path / "photo.jpg", lat=45.0, lon=6.0)
    import_directory(tmp_path, db_conn)
    result = import_directory(tmp_path, db_conn)
    assert result.skipped == 1
    assert result.indexed == 0


def test_import_directory_writes_correct_thumb_status(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    make_jpeg(tmp_path / "photo.jpg", lat=45.0, lon=6.0)
    import_directory(tmp_path, db_conn)
    row = db_conn.execute("SELECT thumb_status FROM photos").fetchone()
    assert row["thumb_status"] == "pending"


def test_import_directory_marks_orphan_when_no_gps(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    make_jpeg(tmp_path / "nogps.jpg", dt_str="2024:07:14 10:00:00")
    import_directory(tmp_path, db_conn)
    row = db_conn.execute("SELECT is_orphan, lat, lon FROM photos").fetchone()
    assert row["is_orphan"] == 1
    assert row["lat"] is None


def test_import_directory_not_orphan_when_has_gps(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    make_jpeg(tmp_path / "gps.jpg", lat=45.0, lon=6.0)
    import_directory(tmp_path, db_conn)
    row = db_conn.execute("SELECT is_orphan FROM photos").fetchone()
    assert row["is_orphan"] == 0


def test_import_directory_stores_absolute_path(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    make_jpeg(tmp_path / "photo.jpg")
    import_directory(tmp_path, db_conn)
    row = db_conn.execute("SELECT file_path FROM photos").fetchone()
    assert Path(row["file_path"]).is_absolute()
