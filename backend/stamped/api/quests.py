import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from stamped.core.db import get_db

router = APIRouter()


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
) -> list[list[float]]:
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")
    rows = conn.execute(
        "SELECT t.lat, t.lon FROM gpx_trackpoints t"
        " JOIN gpx_files f ON f.id = t.gpx_file_id"
        " WHERE f.quest_id = ? ORDER BY t.recorded_at",
        (quest_id,),
    ).fetchall()
    return [[r["lat"], r["lon"]] for r in rows]


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
