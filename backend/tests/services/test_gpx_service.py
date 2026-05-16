import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.gpx_service import import_gpx_directory, scan_gpx_files

_GPX_CONTENT = """\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
  <trk><trkseg>
    <trkpt lat="45.832" lon="6.865"><ele>1200</ele><time>2024-07-14T08:00:00Z</time></trkpt>
    <trkpt lat="45.840" lon="6.872"><ele>1350</ele><time>2024-07-14T09:00:00Z</time></trkpt>
    <trkpt lat="45.851" lon="6.880"><ele>1480</ele><time>2024-07-14T10:30:00Z</time></trkpt>
  </trkseg></trk>
</gpx>"""


def _make_gpx(path: Path, content: str = _GPX_CONTENT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")


@pytest.fixture()
def db_conn() -> Generator[sqlite3.Connection, None, None]:
    init_db()
    with get_connection() as conn:
        yield conn


def test_scan_gpx_files_finds_gpx_recursively(tmp_path: Path) -> None:
    _make_gpx(tmp_path / "a.gpx")
    _make_gpx(tmp_path / "sub" / "b.gpx")
    (tmp_path / "photo.jpg").write_bytes(b"")
    results = scan_gpx_files(tmp_path)
    assert len(results) == 2


def test_import_gpx_directory_indexes_new_file(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    _make_gpx(tmp_path / "track.gpx")
    result = import_gpx_directory(tmp_path, db_conn)
    assert result.indexed == 1
    assert result.errors == 0


def test_import_gpx_directory_writes_gpx_file_row(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    _make_gpx(tmp_path / "track.gpx")
    import_gpx_directory(tmp_path, db_conn)
    row = db_conn.execute("SELECT point_count, recorded_at_start FROM gpx_files").fetchone()
    assert row["point_count"] == 3
    assert row["recorded_at_start"] == "2024-07-14T08:00:00Z"


def test_import_gpx_directory_writes_trackpoints(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    _make_gpx(tmp_path / "track.gpx")
    import_gpx_directory(tmp_path, db_conn)
    count = db_conn.execute("SELECT COUNT(*) FROM gpx_trackpoints").fetchone()[0]
    assert count == 3


def test_import_gpx_directory_skips_duplicate(tmp_path: Path, db_conn: sqlite3.Connection) -> None:
    _make_gpx(tmp_path / "track.gpx")
    import_gpx_directory(tmp_path, db_conn)
    result = import_gpx_directory(tmp_path, db_conn)
    assert result.skipped == 1
    assert result.indexed == 0


def test_import_gpx_directory_trackpoints_linked_to_file(
    tmp_path: Path, db_conn: sqlite3.Connection
) -> None:
    _make_gpx(tmp_path / "track.gpx")
    import_gpx_directory(tmp_path, db_conn)
    gpx_id = db_conn.execute("SELECT id FROM gpx_files").fetchone()["id"]
    count = db_conn.execute(
        "SELECT COUNT(*) FROM gpx_trackpoints WHERE gpx_file_id = ?", (gpx_id,)
    ).fetchone()[0]
    assert count == 3
