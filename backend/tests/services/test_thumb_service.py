import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.thumb_service import (
    ThumbResult,
    process_pending_thumbs,
    process_priority_thumb,
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


def _insert_photo(
    conn: sqlite3.Connection,
    file_path: str,
    file_hash: str,
    thumb_status: str = "pending",
) -> int:
    row = conn.execute(
        "INSERT INTO photos (file_path, file_hash, is_orphan, thumb_status) VALUES (?, ?, 0, ?)",
        (file_path, file_hash, thumb_status),
    )
    conn.commit()
    return row.lastrowid  # type: ignore[return-value]


def test_process_pending_thumbs_empty(db_conn: sqlite3.Connection) -> None:
    result = process_pending_thumbs(db_conn)
    assert result == ThumbResult(done=0, failed=0)


def test_process_pending_thumbs_generates_thumb(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    file_hash = "a" * 64
    _insert_photo(db_conn, str(jpeg), file_hash)
    result = process_pending_thumbs(db_conn)
    assert result.done == 1
    assert result.failed == 0


def test_process_pending_thumbs_updates_status_to_done(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    pid = _insert_photo(db_conn, str(jpeg), "b" * 64)
    process_pending_thumbs(db_conn)
    row = db_conn.execute(
        "SELECT thumb_status, thumb_path FROM photos WHERE id = ?", (pid,)
    ).fetchone()
    assert row["thumb_status"] == "done"
    assert row["thumb_path"] is not None


def test_process_pending_thumbs_marks_error_on_missing_file(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_photo(db_conn, "/nonexistent/photo.jpg", "c" * 64)
    result = process_pending_thumbs(db_conn)
    assert result.failed == 1
    assert result.done == 0
    row = db_conn.execute("SELECT thumb_status FROM photos").fetchone()
    assert row["thumb_status"] == "error"


def test_process_pending_thumbs_skips_non_pending(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    _insert_photo(db_conn, str(jpeg), "d" * 64, thumb_status="done")
    result = process_pending_thumbs(db_conn)
    assert result == ThumbResult(done=0, failed=0)


def test_process_priority_thumb_generates_immediately(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    pid = _insert_photo(db_conn, str(jpeg), "e" * 64)
    success = process_priority_thumb(db_conn, pid)
    assert success is True
    row = db_conn.execute("SELECT thumb_status FROM photos WHERE id = ?", (pid,)).fetchone()
    assert row["thumb_status"] == "done"


def test_process_priority_thumb_returns_false_for_unknown(
    db_conn: sqlite3.Connection,
) -> None:
    result = process_priority_thumb(db_conn, 9999)
    assert result is False


def test_process_priority_thumb_skips_already_done(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    jpeg = make_jpeg(tmp_path / "photo.jpg")
    pid = _insert_photo(db_conn, str(jpeg), "f" * 64, thumb_status="done")
    result = process_priority_thumb(db_conn, pid)
    assert result is True
    row = db_conn.execute("SELECT thumb_status FROM photos WHERE id = ?", (pid,)).fetchone()
    assert row["thumb_status"] == "done"
