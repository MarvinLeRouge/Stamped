import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from stamped.core.config import settings
from stamped.core.fs import get_thumb_path
from stamped.workers.thumb_worker import generate_thumbnail

logger = logging.getLogger(__name__)

_BATCH = 50


@dataclass
class ThumbResult:
    done: int
    failed: int


def _process_one(conn: sqlite3.Connection, photo_id: int, file_path: str, file_hash: str) -> bool:
    conn.execute("UPDATE photos SET thumb_status = 'generating' WHERE id = ?", (photo_id,))
    conn.commit()

    dest = get_thumb_path(file_hash)
    success = generate_thumbnail(Path(file_path), dest, size=settings.thumb_size)

    if success:
        conn.execute(
            "UPDATE photos SET thumb_status = 'done', thumb_path = ? WHERE id = ?",
            (str(dest), photo_id),
        )
    else:
        conn.execute("UPDATE photos SET thumb_status = 'error' WHERE id = ?", (photo_id,))
    conn.commit()
    return success


def process_pending_thumbs(conn: sqlite3.Connection) -> ThumbResult:
    """Process up to _BATCH pending thumbnails. Updates thumb_status in DB."""
    rows = conn.execute(
        "SELECT id, file_path, file_hash FROM photos WHERE thumb_status = 'pending' LIMIT ?",
        (_BATCH,),
    ).fetchall()

    done = failed = 0
    for row in rows:
        if _process_one(conn, row["id"], row["file_path"], row["file_hash"]):
            done += 1
        else:
            failed += 1

    return ThumbResult(done=done, failed=failed)


def process_priority_thumb(conn: sqlite3.Connection, photo_id: int) -> bool:
    """Immediately generate the thumbnail for a single photo, regardless of queue position."""
    row = conn.execute(
        "SELECT file_path, file_hash, thumb_status FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()

    if row is None or row["thumb_status"] == "done":
        return row is not None

    return _process_one(conn, photo_id, row["file_path"], row["file_hash"])
