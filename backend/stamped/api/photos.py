import sqlite3
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from stamped.core.db import get_connection, get_db
from stamped.services.thumb_service import process_priority_thumb

router = APIRouter()


class PhotoSummary(BaseModel):
    id: int
    lat: float | None
    lon: float | None
    captured_at: str | None
    thumb_status: str
    quest_id: int | None
    is_orphan: bool


class PhotoPatch(BaseModel):
    lat: float
    lon: float


@router.get("/photos", response_model=list[PhotoSummary])
def list_photos(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    lat_min: float | None = Query(default=None),
    lat_max: float | None = Query(default=None),
    lon_min: float | None = Query(default=None),
    lon_max: float | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    quest_id: int | None = Query(default=None),
    orphan: bool | None = Query(default=None),
    limit: int = Query(default=500, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[PhotoSummary]:
    conditions: list[str] = []
    params: list[object] = []

    if lat_min is not None:
        conditions.append("lat >= ?")
        params.append(lat_min)
    if lat_max is not None:
        conditions.append("lat <= ?")
        params.append(lat_max)
    if lon_min is not None:
        conditions.append("lon >= ?")
        params.append(lon_min)
    if lon_max is not None:
        conditions.append("lon <= ?")
        params.append(lon_max)
    if date_from is not None:
        conditions.append("captured_at >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("captured_at <= ?")
        params.append(date_to)
    if quest_id is not None:
        conditions.append("quest_id = ?")
        params.append(quest_id)
    if orphan is not None:
        conditions.append("is_orphan = ?")
        params.append(1 if orphan else 0)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    rows = conn.execute(
        f"SELECT id, lat, lon, captured_at, thumb_status, quest_id, is_orphan"
        f" FROM photos {where} ORDER BY captured_at LIMIT ? OFFSET ?",
        params,
    ).fetchall()

    return [
        PhotoSummary(
            id=r["id"],
            lat=r["lat"],
            lon=r["lon"],
            captured_at=r["captured_at"],
            thumb_status=r["thumb_status"],
            quest_id=r["quest_id"],
            is_orphan=bool(r["is_orphan"]),
        )
        for r in rows
    ]


def _get_photo_or_404(conn: sqlite3.Connection, photo_id: int) -> sqlite3.Row:
    row: sqlite3.Row | None = conn.execute(
        "SELECT id, file_path, thumb_path, thumb_status FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return row


@router.patch("/photos/{photo_id}", response_model=PhotoSummary)
def patch_photo(
    photo_id: int,
    body: PhotoPatch,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> PhotoSummary:
    row = conn.execute("SELECT id FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    conn.execute(
        "UPDATE photos SET lat = ?, lon = ?, is_orphan = 0 WHERE id = ?",
        (body.lat, body.lon, photo_id),
    )
    conn.commit()
    r = conn.execute(
        "SELECT id, lat, lon, captured_at, thumb_status, quest_id, is_orphan"
        " FROM photos WHERE id = ?",
        (photo_id,),
    ).fetchone()
    return PhotoSummary(
        id=r["id"],
        lat=r["lat"],
        lon=r["lon"],
        captured_at=r["captured_at"],
        thumb_status=r["thumb_status"],
        quest_id=r["quest_id"],
        is_orphan=bool(r["is_orphan"]),
    )


@router.get("/photos/{photo_id}/original")
async def get_original(
    photo_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Response:
    row = _get_photo_or_404(conn, photo_id)
    return FileResponse(row["file_path"], media_type="image/jpeg")


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


@router.delete("/photos/{photo_id}", status_code=204)
def delete_photo(
    photo_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> None:
    row = conn.execute(
        "SELECT file_hash, thumb_path, quest_id FROM photos WHERE id = ?", (photo_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    conn.execute("INSERT OR IGNORE INTO deleted_photos (file_hash) VALUES (?)", (row["file_hash"],))
    conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))

    if row["quest_id"] is not None:
        conn.execute(
            "UPDATE quests SET photo_count = (SELECT COUNT(*) FROM photos WHERE quest_id = ?)"
            " WHERE id = ?",
            (row["quest_id"], row["quest_id"]),
        )
        conn.execute(
            """UPDATE quests SET
                bbox_lat_min = (SELECT MIN(lat) FROM photos WHERE quest_id = ? AND lat IS NOT NULL),
                bbox_lat_max = (SELECT MAX(lat) FROM photos WHERE quest_id = ? AND lat IS NOT NULL),
                bbox_lon_min = (SELECT MIN(lon) FROM photos WHERE quest_id = ? AND lon IS NOT NULL),
                bbox_lon_max = (SELECT MAX(lon) FROM photos WHERE quest_id = ? AND lon IS NOT NULL)
            WHERE id = ?""",
            (row["quest_id"], row["quest_id"], row["quest_id"], row["quest_id"], row["quest_id"]),
        )
    conn.commit()

    if row["thumb_path"]:
        import pathlib

        thumb = pathlib.Path(row["thumb_path"])
        if thumb.exists():
            thumb.unlink()


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
