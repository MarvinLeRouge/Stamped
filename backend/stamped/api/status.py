import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from stamped.core.db import get_db

router = APIRouter()


class SystemStatus(BaseModel):
    photos_total: int = 0
    thumbs_done: int = 0
    thumbs_pending: int = 0
    orphans: int = 0
    gpx_files: int = 0
    quests: int = 0
    last_index_at: str | None = None


def _get_state(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _count(conn: sqlite3.Connection, query: str) -> int:
    return int(conn.execute(query).fetchone()[0])


@router.get("/status", response_model=SystemStatus)
def get_status(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> SystemStatus:
    return SystemStatus(
        photos_total=_count(conn, "SELECT COUNT(*) FROM photos"),
        thumbs_done=_count(conn, "SELECT COUNT(*) FROM photos WHERE thumb_status = 'done'"),
        thumbs_pending=_count(conn, "SELECT COUNT(*) FROM photos WHERE thumb_status = 'pending'"),
        orphans=_count(conn, "SELECT COUNT(*) FROM photos WHERE is_orphan = 1"),
        gpx_files=_count(conn, "SELECT COUNT(*) FROM gpx_files"),
        quests=_count(conn, "SELECT COUNT(*) FROM quests"),
        last_index_at=_get_state(conn, "last_index_at"),
    )
