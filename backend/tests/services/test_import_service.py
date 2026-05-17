import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.import_service import (
    InterpolationResult,
    compute_hash,
    import_directory,
    interpolate_gps_from_trackpoints,
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


# ── interpolate_gps_from_trackpoints ─────────────────────────────────────────


def _insert_trackpoints(conn: sqlite3.Connection, points: list[tuple[str, float, float]]) -> None:
    """Insert (recorded_at, lat, lon) trackpoints via a fake gpx_file row."""
    gpx_id = conn.execute(
        "INSERT INTO gpx_files (file_path, file_hash, point_count) VALUES ('f.gpx','h',?)",
        (len(points),),
    ).lastrowid
    conn.executemany(
        "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon) VALUES (?,?,?,?)",
        [(gpx_id, t, la, lo) for t, la, lo in points],
    )
    conn.commit()


def _insert_orphan_photo(conn: sqlite3.Connection, captured_at: str, idx: int = 0) -> int:
    row = conn.execute(
        "INSERT INTO photos (file_path, file_hash, captured_at, captured_at_src, is_orphan)"
        " VALUES (?,?,?,'exif',1)",
        (f"p{idx}.jpg", f"h{idx}", captured_at),
    )
    conn.commit()
    return row.lastrowid  # type: ignore[return-value]


def test_interpolate_no_trackpoints_returns_zero(db_conn: sqlite3.Connection) -> None:
    result = interpolate_gps_from_trackpoints(db_conn)
    assert result == InterpolationResult(interpolated=0, still_orphan=0)


def test_interpolate_photo_between_trackpoints_gets_position(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 45.0, 6.0),
            ("2024-07-14T10:00:00Z", 47.0, 8.0),
        ],
    )
    pid = _insert_orphan_photo(db_conn, "2024-07-14T09:00:00Z")
    result = interpolate_gps_from_trackpoints(db_conn)
    assert result.interpolated == 1
    assert result.still_orphan == 0
    row = db_conn.execute(
        "SELECT lat, lon, captured_at_src, is_orphan FROM photos WHERE id=?", (pid,)
    ).fetchone()
    assert abs(row["lat"] - 46.0) < 0.001
    assert abs(row["lon"] - 7.0) < 0.001
    assert row["captured_at_src"] == "gpx_interp"
    assert row["is_orphan"] == 0


def test_interpolate_photo_before_all_trackpoints_stays_orphan(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T10:00:00Z", 45.0, 6.0),
            ("2024-07-14T12:00:00Z", 46.0, 7.0),
        ],
    )
    _insert_orphan_photo(db_conn, "2024-07-14T08:00:00Z")
    result = interpolate_gps_from_trackpoints(db_conn)
    assert result.interpolated == 0
    assert result.still_orphan == 1


def test_interpolate_photo_after_all_trackpoints_stays_orphan(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 45.0, 6.0),
            ("2024-07-14T10:00:00Z", 46.0, 7.0),
        ],
    )
    _insert_orphan_photo(db_conn, "2024-07-14T14:00:00Z")
    result = interpolate_gps_from_trackpoints(db_conn)
    assert result.interpolated == 0
    assert result.still_orphan == 1


def test_interpolate_photo_with_existing_gps_not_touched(
    db_conn: sqlite3.Connection,
) -> None:
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 45.0, 6.0),
            ("2024-07-14T10:00:00Z", 46.0, 7.0),
        ],
    )
    db_conn.execute(
        "INSERT INTO photos (file_path, file_hash, captured_at, captured_at_src, lat, lon, is_orphan)"
        " VALUES ('x.jpg','hx','2024-07-14T09:00:00Z','exif',10.0,20.0,0)"
    )
    db_conn.commit()
    result = interpolate_gps_from_trackpoints(db_conn)
    assert result.interpolated == 0
    row = db_conn.execute("SELECT lat FROM photos").fetchone()
    assert row["lat"] == 10.0


def test_interpolate_midpoint_is_exact(db_conn: sqlite3.Connection) -> None:
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 44.0, 4.0),
            ("2024-07-14T10:00:00Z", 46.0, 6.0),
        ],
    )
    pid = _insert_orphan_photo(db_conn, "2024-07-14T09:00:00Z")
    interpolate_gps_from_trackpoints(db_conn)
    row = db_conn.execute("SELECT lat, lon FROM photos WHERE id=?", (pid,)).fetchone()
    assert abs(row["lat"] - 45.0) < 1e-9
    assert abs(row["lon"] - 5.0) < 1e-9


def test_interpolate_utc_offset_shifts_photo_timestamp(db_conn: sqlite3.Connection) -> None:
    # GPX: 08:00–10:00 UTC. Photo at 10:00 "local" (UTC+2) = 08:00 UTC → hits the range.
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 44.0, 4.0),
            ("2024-07-14T10:00:00Z", 46.0, 6.0),
        ],
    )
    pid = _insert_orphan_photo(db_conn, "2024-07-14T10:00:00Z")  # local CEST
    result = interpolate_gps_from_trackpoints(db_conn, utc_offset_hours=2)
    assert result.interpolated == 1
    row = db_conn.execute("SELECT lat, lon FROM photos WHERE id=?", (pid,)).fetchone()
    assert abs(row["lat"] - 44.0) < 0.001  # 10:00 local = 08:00 UTC → first trackpoint
    assert abs(row["lon"] - 4.0) < 0.001


def test_interpolate_utc_offset_orphan_without_offset(db_conn: sqlite3.Connection) -> None:
    # Same photo would be orphan without the offset (10:00 UTC is beyond trackpoints end).
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 44.0, 4.0),
            ("2024-07-14T09:00:00Z", 45.0, 5.0),
        ],
    )
    _insert_orphan_photo(db_conn, "2024-07-14T10:00:00Z")
    result = interpolate_gps_from_trackpoints(db_conn, utc_offset_hours=0)
    assert result.still_orphan == 1


def test_interpolate_utc_offset_negative(db_conn: sqlite3.Connection) -> None:
    # UTC-5: photo at 03:00 local = 08:00 UTC → within 08:00–10:00 GPX.
    _insert_trackpoints(
        db_conn,
        [
            ("2024-07-14T08:00:00Z", 44.0, 4.0),
            ("2024-07-14T10:00:00Z", 46.0, 6.0),
        ],
    )
    pid = _insert_orphan_photo(db_conn, "2024-07-14T03:00:00Z")  # local UTC-5
    result = interpolate_gps_from_trackpoints(db_conn, utc_offset_hours=-5)
    assert result.interpolated == 1
    row = db_conn.execute("SELECT lat, lon FROM photos WHERE id=?", (pid,)).fetchone()
    assert abs(row["lat"] - 44.0) < 0.001
