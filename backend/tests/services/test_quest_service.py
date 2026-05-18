import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from stamped.core.config import settings
from stamped.core.db import get_connection, init_db
from stamped.services.quest_service import cluster_quests


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
    captured_at: str,
    lat: float | None = 45.0,
    lon: float | None = 6.0,
    file_path: str = "",
    file_hash: str = "",
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO photos (file_path, file_hash, captured_at, captured_at_src, lat, lon, is_orphan)
        VALUES (?, ?, ?, 'exif', ?, ?, ?)
        """,
        (
            file_path or f"photo_{captured_at}.jpg",
            file_hash or f"hash_{captured_at}",
            captured_at,
            lat,
            lon,
            0 if lat is not None else 1,
        ),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def _insert_gpx(
    conn: sqlite3.Connection,
    recorded_at_start: str,
    recorded_at_end: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO gpx_files
            (file_path, file_hash, recorded_at_start, recorded_at_end, point_count)
        VALUES (?, ?, ?, ?, 1)
        """,
        (
            f"track_{recorded_at_start}.gpx",
            f"gpxhash_{recorded_at_start}",
            recorded_at_start,
            recorded_at_end,
        ),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def test_cluster_quests_no_photos(db_conn: sqlite3.Connection) -> None:
    result = cluster_quests(db_conn)
    assert result.quests_created == 0
    assert result.photos_assigned == 0
    assert result.gpx_assigned == 0


def test_cluster_quests_single_group(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T09:00:00Z")
    _insert_photo(db_conn, "2024-07-14T10:30:00Z")
    result = cluster_quests(db_conn)
    assert result.quests_created == 1
    assert result.photos_assigned == 3


def test_cluster_quests_two_groups_with_gap(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T09:00:00Z")
    # 7h gap — exceeds the 6h threshold
    _insert_photo(db_conn, "2024-07-14T16:00:00Z")
    result = cluster_quests(db_conn)
    assert result.quests_created == 2
    assert result.photos_assigned == 3


def test_cluster_quests_photo_count(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T09:00:00Z")
    cluster_quests(db_conn)
    row = db_conn.execute("SELECT photo_count FROM quests").fetchone()
    assert row["photo_count"] == 2


def test_cluster_quests_started_ended_at(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T10:30:00Z")
    cluster_quests(db_conn)
    row = db_conn.execute("SELECT started_at, ended_at FROM quests").fetchone()
    assert row["started_at"] == "2024-07-14T08:00:00Z"
    assert row["ended_at"] == "2024-07-14T10:30:00Z"


def test_cluster_quests_auto_name(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    cluster_quests(db_conn)
    row = db_conn.execute("SELECT auto_name FROM quests").fetchone()
    assert row["auto_name"] == "Quest 2024-07-14"


def test_cluster_quests_bbox(db_conn: sqlite3.Connection) -> None:
    _insert_photo(db_conn, "2024-07-14T08:00:00Z", lat=45.0, lon=6.0)
    _insert_photo(db_conn, "2024-07-14T09:00:00Z", lat=46.0, lon=7.0)
    cluster_quests(db_conn)
    row = db_conn.execute(
        "SELECT bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max FROM quests"
    ).fetchone()
    assert row["bbox_lat_min"] == pytest.approx(45.0)
    assert row["bbox_lat_max"] == pytest.approx(46.0)
    assert row["bbox_lon_min"] == pytest.approx(6.0)
    assert row["bbox_lon_max"] == pytest.approx(7.0)


def test_cluster_quests_assigns_quest_id_to_photos(db_conn: sqlite3.Connection) -> None:
    pid = _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    cluster_quests(db_conn)
    row = db_conn.execute("SELECT quest_id FROM photos WHERE id = ?", (pid,)).fetchone()
    assert row["quest_id"] is not None


def test_cluster_quests_gpx_overlap(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T10:30:00Z")
    _insert_gpx(db_conn, "2024-07-14T07:55:00Z", "2024-07-14T11:00:00Z")
    result = cluster_quests(db_conn)
    assert result.gpx_assigned == 1
    row = db_conn.execute("SELECT has_gpx FROM quests").fetchone()
    assert row["has_gpx"] == 1


def test_cluster_quests_gpx_no_overlap(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    # GPX from the next day — no overlap
    _insert_gpx(db_conn, "2024-07-15T08:00:00Z", "2024-07-15T12:00:00Z")
    result = cluster_quests(db_conn)
    assert result.gpx_assigned == 0
    row = db_conn.execute("SELECT has_gpx FROM quests").fetchone()
    assert row["has_gpx"] == 0


def test_cluster_quests_gpx_overlap_with_utc_offset(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Photos stored as local CEST (UTC+2): 10:00–12:00 local = 08:00–10:00 UTC.
    # GPX in true UTC: 07:55–09:30. The GPX ends before the local photo window
    # starts (09:30 < 10:00), so without offset correction there is no overlap.
    # With offset=2 the corrected quest window (08:00–10:00 UTC) overlaps the GPX.
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    monkeypatch.setattr(settings, "camera_utc_offset_hours", 2)
    _insert_photo(db_conn, "2024-07-14T10:00:00Z")  # local CEST
    _insert_photo(db_conn, "2024-07-14T12:00:00Z")  # local CEST
    _insert_gpx(db_conn, "2024-07-14T07:55:00Z", "2024-07-14T09:30:00Z")  # UTC
    result = cluster_quests(db_conn)
    assert result.gpx_assigned == 1
    row = db_conn.execute("SELECT has_gpx FROM quests").fetchone()
    assert row["has_gpx"] == 1


def test_cluster_quests_gpx_no_overlap_without_utc_offset(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same data as above but offset=0: quest window stays at 10:00–12:00 and the
    # GPX ends at 09:30 → no overlap (09:30 < 10:00).
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    monkeypatch.setattr(settings, "camera_utc_offset_hours", 0)
    _insert_photo(db_conn, "2024-07-14T10:00:00Z")
    _insert_photo(db_conn, "2024-07-14T12:00:00Z")
    _insert_gpx(db_conn, "2024-07-14T07:55:00Z", "2024-07-14T09:30:00Z")  # UTC
    result = cluster_quests(db_conn)
    assert result.gpx_assigned == 0


def test_cluster_quests_idempotent(
    db_conn: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "quest_gap_hours", 6)
    _insert_photo(db_conn, "2024-07-14T08:00:00Z")
    _insert_photo(db_conn, "2024-07-14T09:00:00Z")
    cluster_quests(db_conn)
    result = cluster_quests(db_conn)
    assert result.quests_created == 1
    count = db_conn.execute("SELECT COUNT(*) FROM quests").fetchone()[0]
    assert count == 1
