import sqlite3
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse, Response

from stamped.core.db import get_connection, get_db
from stamped.services.thumb_service import process_priority_thumb

router = APIRouter()


def _get_photo_or_404(conn: sqlite3.Connection, photo_id: int) -> sqlite3.Row:
    row: sqlite3.Row | None = conn.execute(
        "SELECT id, thumb_path, thumb_status FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return row


@router.get("/photos/{photo_id}/thumb")
async def get_thumbnail(
    photo_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Response:
    row = _get_photo_or_404(conn, photo_id)

    if row["thumb_status"] == "done" and row["thumb_path"]:
        return FileResponse(row["thumb_path"], media_type="image/jpeg")

    return Response(
        status_code=202,
        headers={"X-Thumb-Status": row["thumb_status"] or "pending"},
    )


def _priority_task(photo_id: int) -> None:
    with get_connection() as conn:
        process_priority_thumb(conn, photo_id)


@router.post("/photos/{photo_id}/thumb/priority")
async def priority_thumbnail(
    photo_id: int,
    background_tasks: BackgroundTasks,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> dict[str, str]:
    _get_photo_or_404(conn, photo_id)
    background_tasks.add_task(_priority_task, photo_id)
    return {"status": "queued"}
