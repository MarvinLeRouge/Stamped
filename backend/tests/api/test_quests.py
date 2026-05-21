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
def client() -> TestClient:
    init_db()
    return TestClient(app)


def _seeded_client(tmp_path: Path) -> TestClient:
    """Return a TestClient whose DB already has one quest."""
    init_db()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO quests
                    (auto_name, started_at, ended_at, photo_count, has_gpx)
                VALUES ('Quest 2024-07-14', '2024-07-14T08:00:00Z', '2024-07-14T10:30:00Z', 3, 0)
                """
            )
            conn.commit()
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def test_get_quests_empty(client: TestClient) -> None:
    r = client.get("/api/quests")
    assert r.status_code == 200
    assert r.json() == []


def test_get_quests_returns_list(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        r = c.get("/api/quests")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


def test_get_quests_shape(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        r = c.get("/api/quests")
        quest = r.json()[0]
        assert set(quest.keys()) == {
            "id",
            "name",
            "auto_name",
            "started_at",
            "ended_at",
            "photo_count",
            "has_gpx",
            "bbox_lat_min",
            "bbox_lat_max",
            "bbox_lon_min",
            "bbox_lon_max",
        }
    finally:
        app.dependency_overrides.clear()


def test_get_quests_values(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest = c.get("/api/quests").json()[0]
        assert quest["auto_name"] == "Quest 2024-07-14"
        assert quest["started_at"] == "2024-07-14T08:00:00Z"
        assert quest["photo_count"] == 3
        assert quest["has_gpx"] is False
        assert quest["name"] is None
    finally:
        app.dependency_overrides.clear()


# ── GET /api/quests/{id}/trackpoints ─────────────────────────────────────────


def _trackpoints_client(tmp_path: Path) -> tuple[TestClient, int]:
    """Return a client with one quest and two GPX files (two segments)."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-01-01T00:00:00Z', '2024-01-01T02:00:00Z', 0, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'a.gpx', 'hash-a')",
            (quest_id,),
        )
        gpx1: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'b.gpx', 'hash-b')",
            (quest_id,),
        )
        gpx2: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.executemany(
            "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon) VALUES (?,?,?,?)",
            [
                (gpx1, "2024-01-01T08:00:00Z", 44.0, 6.0),
                (gpx1, "2024-01-01T08:10:00Z", 44.1, 6.1),
                (gpx2, "2024-01-01T10:00:00Z", 45.0, 7.0),
                (gpx2, "2024-01-01T10:10:00Z", 45.1, 7.1),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_get_trackpoints_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    c = TestClient(app)
    r = c.get("/api/quests/999/trackpoints")
    assert r.status_code == 404


def test_get_trackpoints_returns_two_segments(tmp_path: Path) -> None:
    c, quest_id = _trackpoints_client(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/trackpoints")
        assert r.status_code == 200
        segments = r.json()
        assert len(segments) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_trackpoints_segment_coordinates(tmp_path: Path) -> None:
    c, quest_id = _trackpoints_client(tmp_path)
    try:
        segments = c.get(f"/api/quests/{quest_id}/trackpoints").json()
        assert segments[0][0] == [44.0, 6.0]
        assert segments[0][1] == [44.1, 6.1]
        assert segments[1][0] == [45.0, 7.0]
        assert segments[1][1] == [45.1, 7.1]
    finally:
        app.dependency_overrides.clear()


def test_get_trackpoints_no_gpx_returns_empty(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.get(f"/api/quests/{quest_id}/trackpoints")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


# ── GET /api/quests/{id}/photos ───────────────────────────────────────────────


def _photos_client(tmp_path: Path) -> tuple[TestClient, int]:
    """Return a client with one quest and two photos."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 2, 0)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.executemany(
            "INSERT INTO photos"
            " (file_path, file_hash, captured_at, thumb_status, quest_id, is_orphan)"
            " VALUES (?, ?, ?, 'done', ?, 0)",
            [
                ("/img/a.jpg", "hash-a", "2024-06-01T08:10:00Z", quest_id),
                ("/img/b.jpg", "hash-b", "2024-06-01T09:00:00Z", quest_id),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_get_quest_photos_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    r = TestClient(app).get("/api/quests/999/photos")
    assert r.status_code == 404


def test_get_quest_photos_returns_two_items(tmp_path: Path) -> None:
    c, quest_id = _photos_client(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/photos")
        assert r.status_code == 200
        assert len(r.json()) == 2
    finally:
        app.dependency_overrides.clear()


def test_get_quest_photos_ordered_by_captured_at(tmp_path: Path) -> None:
    c, quest_id = _photos_client(tmp_path)
    try:
        photos = c.get(f"/api/quests/{quest_id}/photos").json()
        assert photos[0]["captured_at"] < photos[1]["captured_at"]
    finally:
        app.dependency_overrides.clear()


def test_get_quest_photos_shape(tmp_path: Path) -> None:
    c, quest_id = _photos_client(tmp_path)
    try:
        photo = c.get(f"/api/quests/{quest_id}/photos").json()[0]
        assert set(photo.keys()) == {"id", "lat", "lon", "captured_at", "thumb_status", "is_orphan"}
    finally:
        app.dependency_overrides.clear()


def test_get_quest_photos_no_photos_returns_empty(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.get(f"/api/quests/{quest_id}/photos")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


# ── GET /api/quests/{id}/gpx ──────────────────────────────────────────────────


def _gpx_client_single(tmp_path: Path) -> tuple[TestClient, int]:
    """Quest with one real GPX file on disk."""
    init_db()
    gpx_file = tmp_path / "track.gpx"
    gpx_file.write_text(
        '<?xml version="1.0"?><gpx version="1.1" creator="test"></gpx>', encoding="utf-8"
    )

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Quest GPX', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 0, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, ?, 'h1')",
            (quest_id, str(gpx_file)),
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def _gpx_client_multi(tmp_path: Path) -> tuple[TestClient, int]:
    """Quest with two GPX files — response must be generated from trackpoints."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Quest Multi', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 0, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'a.gpx', 'ha')",
            (quest_id,),
        )
        gpx1: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'b.gpx', 'hb')",
            (quest_id,),
        )
        gpx2: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.executemany(
            "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon) VALUES (?,?,?,?)",
            [
                (gpx1, "2024-06-01T08:00:00Z", 44.0, 6.0),
                (gpx2, "2024-06-01T09:00:00Z", 45.0, 7.0),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_get_gpx_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    r = TestClient(app).get("/api/quests/999/gpx")
    assert r.status_code == 404


def test_get_gpx_no_gpx_file_returns_404(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.get(f"/api/quests/{quest_id}/gpx")
        assert r.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_get_gpx_single_file_returns_gpx_content_type(tmp_path: Path) -> None:
    c, quest_id = _gpx_client_single(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/gpx")
        assert r.status_code == 200
        assert "gpx" in r.headers["content-type"]
    finally:
        app.dependency_overrides.clear()


def test_get_gpx_single_file_has_attachment_header(tmp_path: Path) -> None:
    c, quest_id = _gpx_client_single(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/gpx")
        assert "attachment" in r.headers["content-disposition"]
        assert ".gpx" in r.headers["content-disposition"]
    finally:
        app.dependency_overrides.clear()


def test_get_gpx_multi_file_returns_valid_xml(tmp_path: Path) -> None:
    c, quest_id = _gpx_client_multi(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/gpx")
        assert r.status_code == 200
        import xml.etree.ElementTree as ET

        root = ET.fromstring(r.content)
        assert root.tag.endswith("gpx")
    finally:
        app.dependency_overrides.clear()


def test_get_gpx_multi_file_contains_two_tracks(tmp_path: Path) -> None:
    c, quest_id = _gpx_client_multi(tmp_path)
    try:
        r = c.get(f"/api/quests/{quest_id}/gpx")
        import xml.etree.ElementTree as ET

        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}
        root = ET.fromstring(r.content)
        tracks = root.findall("gpx:trk", ns)
        assert len(tracks) == 2
    finally:
        app.dependency_overrides.clear()


# ── PATCH /api/quests/{id} ────────────────────────────────────────────────────


def test_patch_quest_unknown_returns_404(tmp_path: Path) -> None:
    init_db()
    r = TestClient(app).patch("/api/quests/999", json={"name": "X"})
    assert r.status_code == 404


def test_patch_quest_sets_name(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.patch(f"/api/quests/{quest_id}", json={"name": "Mon aventure"})
        assert r.status_code == 200
        assert r.json()["name"] == "Mon aventure"
    finally:
        app.dependency_overrides.clear()


def test_patch_quest_clears_name_with_null(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        c.patch(f"/api/quests/{quest_id}", json={"name": "Mon aventure"})
        r = c.patch(f"/api/quests/{quest_id}", json={"name": None})
        assert r.status_code == 200
        assert r.json()["name"] is None
    finally:
        app.dependency_overrides.clear()


def test_patch_quest_strips_whitespace_to_null(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.patch(f"/api/quests/{quest_id}", json={"name": "   "})
        assert r.status_code == 200
        assert r.json()["name"] is None
    finally:
        app.dependency_overrides.clear()


def test_patch_quest_returns_full_quest_shape(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        quest = c.patch(f"/api/quests/{quest_id}", json={"name": "Test"}).json()
        assert set(quest.keys()) == {
            "id",
            "name",
            "auto_name",
            "started_at",
            "ended_at",
            "photo_count",
            "has_gpx",
            "bbox_lat_min",
            "bbox_lat_max",
            "bbox_lon_min",
            "bbox_lon_max",
        }
    finally:
        app.dependency_overrides.clear()


# ── POST /api/quests/{id}/place ───────────────────────────────────────────────


def _place_client(tmp_path: Path) -> tuple[TestClient, int]:
    """Quest with 3 orphan photos and 3 trackpoints for median test."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 3, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'a.gpx', 'hh')",
            (quest_id,),
        )
        gpx_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.executemany(
            "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon) VALUES (?,?,?,?)",
            [
                (gpx_id, "2024-06-01T08:00:00Z", 44.0, 6.0),
                (gpx_id, "2024-06-01T09:00:00Z", 45.0, 7.0),  # median
                (gpx_id, "2024-06-01T10:00:00Z", 46.0, 8.0),
            ],
        )
        conn.executemany(
            "INSERT INTO photos (file_path, file_hash, captured_at, thumb_status, quest_id, is_orphan)"
            " VALUES (?, ?, ?, 'done', ?, 1)",
            [
                ("/a.jpg", "ha", "2024-06-01T08:30:00Z", quest_id),
                ("/b.jpg", "hb", "2024-06-01T09:30:00Z", quest_id),
                ("/c.jpg", "hc", "2024-06-01T09:45:00Z", quest_id),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_place_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    r = TestClient(app).post("/api/quests/999/place", json={})
    assert r.status_code == 404


def test_place_no_gps_no_body_returns_422(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.post(f"/api/quests/{quest_id}/place", json={})
        assert r.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_place_explicit_coords_places_all_orphans(tmp_path: Path) -> None:
    c, quest_id = _place_client(tmp_path)
    try:
        r = c.post(f"/api/quests/{quest_id}/place", json={"lat": 43.0, "lon": 5.5})
        assert r.status_code == 200
        assert r.json()["placed"] == 3
        assert r.json()["lat"] == pytest.approx(43.0)
        assert r.json()["lon"] == pytest.approx(5.5)
    finally:
        app.dependency_overrides.clear()


def test_place_median_from_geolocated_photos(tmp_path: Path) -> None:
    """_median_point falls back to geolocated photos when no trackpoints exist."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 1, 0)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO photos (file_path, file_hash, captured_at, thumb_status, quest_id,"
            " is_orphan, lat, lon) VALUES ('p.jpg', 'hq', '2024-06-01T09:00:00Z', 'done', ?, 0,"
            " 43.0, 5.5)",
            (quest_id,),
        )
        conn.execute(
            "INSERT INTO photos (file_path, file_hash, captured_at, thumb_status, quest_id,"
            " is_orphan) VALUES ('o.jpg', 'ho', '2024-06-01T08:00:00Z', 'done', ?, 1)",
            (quest_id,),
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    try:
        c = TestClient(app)
        r = c.post(f"/api/quests/{quest_id}/place", json={})
        assert r.status_code == 200
        assert r.json()["lat"] == pytest.approx(43.0)
        assert r.json()["lon"] == pytest.approx(5.5)
    finally:
        app.dependency_overrides.clear()


def test_place_median_from_trackpoints(tmp_path: Path) -> None:
    c, quest_id = _place_client(tmp_path)
    try:
        r = c.post(f"/api/quests/{quest_id}/place", json={})
        assert r.status_code == 200
        assert r.json()["placed"] == 3
        assert r.json()["lat"] == pytest.approx(45.0)
        assert r.json()["lon"] == pytest.approx(7.0)
    finally:
        app.dependency_overrides.clear()


def test_place_clears_orphan_flag(tmp_path: Path) -> None:
    c, quest_id = _place_client(tmp_path)
    try:
        c.post(f"/api/quests/{quest_id}/place", json={"lat": 44.0, "lon": 6.0})
        with get_connection() as conn:
            remaining = conn.execute(
                "SELECT COUNT(*) FROM photos WHERE quest_id = ? AND is_orphan = 1", (quest_id,)
            ).fetchone()[0]
        assert remaining == 0
    finally:
        app.dependency_overrides.clear()


def test_place_already_placed_quest_places_zero(tmp_path: Path) -> None:
    c, quest_id = _place_client(tmp_path)
    try:
        c.post(f"/api/quests/{quest_id}/place", json={"lat": 44.0, "lon": 6.0})
        r = c.post(f"/api/quests/{quest_id}/place", json={"lat": 44.0, "lon": 6.0})
        assert r.json()["placed"] == 0
    finally:
        app.dependency_overrides.clear()


def test_place_updates_quest_bbox(tmp_path: Path) -> None:
    c, quest_id = _place_client(tmp_path)
    try:
        c.post(f"/api/quests/{quest_id}/place", json={"lat": 44.0, "lon": 6.0})
        with get_connection() as conn:
            row = conn.execute(
                "SELECT bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max"
                " FROM quests WHERE id = ?",
                (quest_id,),
            ).fetchone()
        assert row["bbox_lat_min"] is not None
        assert row["bbox_lat_max"] is not None
    finally:
        app.dependency_overrides.clear()


# ── GET /api/quests/{id}/elevation ───────────────────────────────────────────


def _elevation_client(tmp_path: Path) -> tuple[TestClient, int]:
    """Quest with one GPX file containing 3 trackpoints with altitude."""
    init_db()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quests (auto_name, started_at, ended_at, photo_count, has_gpx)"
            " VALUES ('Q', '2024-06-01T08:00:00Z', '2024-06-01T10:00:00Z', 0, 1)"
        )
        quest_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO gpx_files (quest_id, file_path, file_hash) VALUES (?, 'a.gpx', 'hh')",
            (quest_id,),
        )
        gpx_id: int = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.executemany(
            "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon, alt)"
            " VALUES (?,?,?,?,?)",
            [
                (gpx_id, "2024-06-01T08:00:00Z", 44.0, 6.0, 100.0),
                (gpx_id, "2024-06-01T08:10:00Z", 44.001, 6.001, 150.0),
                (gpx_id, "2024-06-01T08:20:00Z", 44.002, 6.002, 200.0),
            ],
        )
        conn.commit()

    def _override_db() -> Generator[sqlite3.Connection, None, None]:
        with get_connection() as conn:
            yield conn

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app), quest_id


def test_get_elevation_unknown_quest_returns_404(tmp_path: Path) -> None:
    init_db()
    r = TestClient(app).get("/api/quests/999/elevation")
    assert r.status_code == 404


def test_get_elevation_no_gpx_returns_empty(tmp_path: Path) -> None:
    c = _seeded_client(tmp_path)
    try:
        quest_id = c.get("/api/quests").json()[0]["id"]
        r = c.get(f"/api/quests/{quest_id}/elevation")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        app.dependency_overrides.clear()


def test_get_elevation_returns_correct_count(tmp_path: Path) -> None:
    c, quest_id = _elevation_client(tmp_path)
    try:
        points = c.get(f"/api/quests/{quest_id}/elevation").json()
        assert len(points) == 3
    finally:
        app.dependency_overrides.clear()


def test_get_elevation_first_point_distance_zero(tmp_path: Path) -> None:
    c, quest_id = _elevation_client(tmp_path)
    try:
        points = c.get(f"/api/quests/{quest_id}/elevation").json()
        assert points[0]["d"] == 0.0
        assert points[0]["alt"] == 100.0
    finally:
        app.dependency_overrides.clear()


def test_get_elevation_distance_increases(tmp_path: Path) -> None:
    c, quest_id = _elevation_client(tmp_path)
    try:
        points = c.get(f"/api/quests/{quest_id}/elevation").json()
        assert points[1]["d"] > 0
        assert points[2]["d"] > points[1]["d"]
    finally:
        app.dependency_overrides.clear()


def test_get_elevation_has_timestamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from stamped.core.config import settings as cfg

    monkeypatch.setattr(cfg, "camera_utc_offset_hours", 0)
    c, quest_id = _elevation_client(tmp_path)
    try:
        points = c.get(f"/api/quests/{quest_id}/elevation").json()
        assert points[0]["t"] == "2024-06-01T08:00:00Z"
    finally:
        app.dependency_overrides.clear()


def test_get_elevation_timestamp_shifted_by_utc_offset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from stamped.core.config import settings as cfg

    monkeypatch.setattr(cfg, "camera_utc_offset_hours", 2)
    c, quest_id = _elevation_client(tmp_path)
    try:
        points = c.get(f"/api/quests/{quest_id}/elevation").json()
        assert points[0]["t"] == "2024-06-01T10:00:00Z"
    finally:
        app.dependency_overrides.clear()
