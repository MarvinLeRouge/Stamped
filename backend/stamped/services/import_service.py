import bisect
import hashlib
import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from stamped.workers.exif_worker import ExifData, extract_exif

logger = logging.getLogger(__name__)

_JPEG_SUFFIXES = {".jpg", ".jpeg", ".JPG", ".JPEG"}
_HASH_CHUNK = 65536


@dataclass
class ImportResult:
    indexed: int
    skipped: int
    errors: int


@dataclass
class InterpolationResult:
    interpolated: int
    still_orphan: int


def scan_jpegs(directory: Path) -> list[Path]:
    """Recursively find all JPEG files under directory."""
    return [p for p in directory.rglob("*") if p.suffix in _JPEG_SUFFIXES and p.is_file()]


def compute_hash(path: Path) -> str:
    """Return SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_HASH_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def _hash_exists(conn: sqlite3.Connection, file_hash: str) -> bool:
    row = conn.execute("SELECT 1 FROM photos WHERE file_hash = ?", (file_hash,)).fetchone()
    return row is not None


def _insert_photo(
    conn: sqlite3.Connection, file_path: Path, file_hash: str, exif: ExifData
) -> None:
    conn.execute(
        """
        INSERT INTO photos
            (file_path, file_hash, captured_at, captured_at_src,
             lat, lon, camera_make, camera_model, is_orphan, thumb_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        """,
        (
            str(file_path.resolve()),
            file_hash,
            exif.captured_at,
            "exif" if exif.captured_at else "unknown",
            exif.lat,
            exif.lon,
            exif.camera_make,
            exif.camera_model,
            1 if exif.lat is None else 0,
        ),
    )


def interpolate_gps_from_trackpoints(conn: sqlite3.Connection) -> InterpolationResult:
    """
    For each photo that has a timestamp but no GPS, attempt to interpolate
    lat/lon from GPX trackpoints using bisect.

    On success: sets lat, lon, captured_at_src='gpx_interp', is_orphan=0.
    Photos outside the trackpoint time range remain is_orphan=1.
    """
    trackpoints = conn.execute(
        "SELECT recorded_at, lat, lon FROM gpx_trackpoints ORDER BY recorded_at"
    ).fetchall()

    if not trackpoints:
        return InterpolationResult(interpolated=0, still_orphan=0)

    times = [tp["recorded_at"] for tp in trackpoints]

    photos = conn.execute(
        "SELECT id, captured_at FROM photos WHERE lat IS NULL AND captured_at IS NOT NULL"
    ).fetchall()

    interpolated = still_orphan = 0

    for photo in photos:
        ts = photo["captured_at"]
        i = bisect.bisect_left(times, ts)

        if i == 0 or i >= len(trackpoints):
            still_orphan += 1
            continue

        a, b = trackpoints[i - 1], trackpoints[i]
        ta = datetime.strptime(a["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        tb = datetime.strptime(b["recorded_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        tt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)

        span = (tb - ta).total_seconds()
        t = (tt - ta).total_seconds() / span if span else 0.0

        lat = a["lat"] + t * (b["lat"] - a["lat"])
        lon = a["lon"] + t * (b["lon"] - a["lon"])

        conn.execute(
            "UPDATE photos SET lat=?, lon=?, captured_at_src='gpx_interp', is_orphan=0 WHERE id=?",
            (lat, lon, photo["id"]),
        )
        interpolated += 1

    if interpolated:
        conn.commit()

    return InterpolationResult(interpolated=interpolated, still_orphan=still_orphan)


def import_directory(directory: Path, conn: sqlite3.Connection) -> ImportResult:
    """
    Scan directory for JPEGs, deduplicate by hash, write new photos to DB.
    Photos without GPS coordinates are marked is_orphan=1.
    """
    paths = scan_jpegs(directory)
    indexed = skipped = errors = 0

    for path in paths:
        try:
            file_hash = compute_hash(path)
            if _hash_exists(conn, file_hash):
                skipped += 1
                continue
            exif = extract_exif(path)
            _insert_photo(conn, path, file_hash, exif)
            indexed += 1
        except Exception:
            logger.exception("Failed to import %s", path)
            errors += 1

    if indexed:
        conn.commit()

    return ImportResult(indexed=indexed, skipped=skipped, errors=errors)
