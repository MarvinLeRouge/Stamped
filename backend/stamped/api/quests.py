import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stamped.core.db import get_db

router = APIRouter()


class QuestPhotoItem(BaseModel):
    id: int
    lat: float | None
    lon: float | None
    captured_at: str | None
    thumb_status: str
    is_orphan: bool


class QuestResponse(BaseModel):
    id: int
    name: str | None
    auto_name: str
    started_at: str | None
    ended_at: str | None
    photo_count: int
    has_gpx: bool
    bbox_lat_min: float | None
    bbox_lat_max: float | None
    bbox_lon_min: float | None
    bbox_lon_max: float | None


@router.get("/quests/{quest_id}/trackpoints")
def get_quest_trackpoints(
    quest_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> list[list[list[float]]]:
    """Return trackpoints grouped by GPX file — one segment per file."""
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    rows = conn.execute(
        "SELECT t.gpx_file_id, t.lat, t.lon FROM gpx_trackpoints t"
        " JOIN gpx_files f ON f.id = t.gpx_file_id"
        " WHERE f.quest_id = ? ORDER BY t.gpx_file_id, t.recorded_at",
        (quest_id,),
    ).fetchall()
    segments: dict[int, list[list[float]]] = {}
    for r in rows:
        fid = r["gpx_file_id"]
        if fid not in segments:
            segments[fid] = []
        segments[fid].append([r["lat"], r["lon"]])
    return list(segments.values())


@router.get("/quests/{quest_id}/photos", response_model=list[QuestPhotoItem])
def get_quest_photos(
    quest_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> list[QuestPhotoItem]:
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    rows = conn.execute(
        "SELECT id, lat, lon, captured_at, thumb_status, is_orphan"
        " FROM photos WHERE quest_id = ? ORDER BY captured_at",
        (quest_id,),
    ).fetchall()
    return [
        QuestPhotoItem(
            id=r["id"],
            lat=r["lat"],
            lon=r["lon"],
            captured_at=r["captured_at"],
            thumb_status=r["thumb_status"],
            is_orphan=bool(r["is_orphan"]),
        )
        for r in rows
    ]


class QuestPatch(BaseModel):
    name: str | None


@router.patch("/quests/{quest_id}", response_model=QuestResponse)
def patch_quest(
    quest_id: int,
    body: QuestPatch,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> QuestResponse:
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    name = body.name.strip() if body.name and body.name.strip() else None
    conn.execute("UPDATE quests SET name = ? WHERE id = ?", (name, quest_id))
    conn.commit()
    row = conn.execute("SELECT * FROM quests WHERE id = ?", (quest_id,)).fetchone()
    return QuestResponse(
        id=row["id"],
        name=row["name"],
        auto_name=row["auto_name"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        photo_count=row["photo_count"],
        has_gpx=bool(row["has_gpx"]),
        bbox_lat_min=row["bbox_lat_min"],
        bbox_lat_max=row["bbox_lat_max"],
        bbox_lon_min=row["bbox_lon_min"],
        bbox_lon_max=row["bbox_lon_max"],
    )


@router.get("/quests", response_model=list[QuestResponse])
def get_quests(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> list[QuestResponse]:
    rows = conn.execute("SELECT * FROM quests ORDER BY started_at").fetchall()
    return [
        QuestResponse(
            id=row["id"],
            name=row["name"],
            auto_name=row["auto_name"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            photo_count=row["photo_count"],
            has_gpx=bool(row["has_gpx"]),
            bbox_lat_min=row["bbox_lat_min"],
            bbox_lat_max=row["bbox_lat_max"],
            bbox_lon_min=row["bbox_lon_min"],
            bbox_lon_max=row["bbox_lon_max"],
        )
        for row in rows
    ]
