import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
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
