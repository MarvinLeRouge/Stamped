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


@router.get("/status", response_model=SystemStatus)
def get_status(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> SystemStatus:
    return SystemStatus(
        photos_total=int(_get_state(conn, "photos_total") or 0),
        thumbs_done=int(_get_state(conn, "thumbs_done") or 0),
        thumbs_pending=int(_get_state(conn, "thumbs_pending") or 0),
        orphans=int(_get_state(conn, "orphans_count") or 0),
        gpx_files=int(_get_state(conn, "gpx_files") or 0),
        quests=int(_get_state(conn, "quests") or 0),
        last_index_at=_get_state(conn, "last_index_at"),
    )
