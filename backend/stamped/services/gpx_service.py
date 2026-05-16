import hashlib
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from stamped.workers.gpx_worker import GpxData, parse_gpx

logger = logging.getLogger(__name__)

_GPX_SUFFIX = ".gpx"
_HASH_CHUNK = 65536


@dataclass
class GpxImportResult:
    indexed: int
    skipped: int
    errors: int


def scan_gpx_files(directory: Path) -> list[Path]:
    """Recursively find all GPX files under directory."""
    return [p for p in directory.rglob("*.gpx") if p.is_file()]


def _compute_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _hash_exists(conn: sqlite3.Connection, file_hash: str) -> bool:
    row = conn.execute("SELECT 1 FROM gpx_files WHERE file_hash = ?", (file_hash,)).fetchone()
    return row is not None


def _insert_gpx_file(conn: sqlite3.Connection, path: Path, file_hash: str, data: GpxData) -> int:
    cursor = conn.execute(
        """
        INSERT INTO gpx_files
            (file_path, file_hash, recorded_at_start, recorded_at_end,
             point_count, total_distance_m, elevation_gain_m)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(path.resolve()),
            file_hash,
            data.recorded_at_start,
            data.recorded_at_end,
            data.point_count,
            data.total_distance_m,
            data.elevation_gain_m,
        ),
    )
    return cursor.lastrowid  # type: ignore[return-value]


def _insert_trackpoints(conn: sqlite3.Connection, gpx_file_id: int, data: GpxData) -> None:
    conn.executemany(
        "INSERT INTO gpx_trackpoints (gpx_file_id, recorded_at, lat, lon, alt) VALUES (?,?,?,?,?)",
        [(gpx_file_id, tp.recorded_at, tp.lat, tp.lon, tp.alt) for tp in data.trackpoints],
    )


def import_gpx_directory(directory: Path, conn: sqlite3.Connection) -> GpxImportResult:
    """Scan directory for GPX files, deduplicate by hash, write to DB."""
    paths = scan_gpx_files(directory)
    indexed = skipped = errors = 0

    for path in paths:
        try:
            file_hash = _compute_hash(path)
            if _hash_exists(conn, file_hash):
                skipped += 1
                continue
            data = parse_gpx(path)
            if data is None:
                errors += 1
                continue
            gpx_file_id = _insert_gpx_file(conn, path, file_hash, data)
            _insert_trackpoints(conn, gpx_file_id, data)
            indexed += 1
        except Exception:
            logger.exception("Failed to import GPX %s", path)
            errors += 1

    if indexed:
        conn.commit()

    return GpxImportResult(indexed=indexed, skipped=skipped, errors=errors)
