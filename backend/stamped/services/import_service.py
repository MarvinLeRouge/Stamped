import hashlib
import logging
import sqlite3
from dataclasses import dataclass
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
