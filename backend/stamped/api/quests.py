import math
import sqlite3
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from stamped.core.config import settings
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


class QuestPlaceBody(BaseModel):
    lat: float | None = None
    lon: float | None = None


class QuestPlaceResponse(BaseModel):
    placed: int
    lat: float
    lon: float


def _median_point(conn: sqlite3.Connection, quest_id: int) -> tuple[float, float] | None:
    """Return the chronological median GPS point for a quest (trackpoints + geolocated photos)."""
    points: list[tuple[str, float, float]] = []

    rows = conn.execute(
        "SELECT t.recorded_at, t.lat, t.lon FROM gpx_trackpoints t"
        " JOIN gpx_files f ON f.id = t.gpx_file_id"
        " WHERE f.quest_id = ? ORDER BY t.recorded_at",
        (quest_id,),
    ).fetchall()
    for r in rows:
        points.append((r["recorded_at"], r["lat"], r["lon"]))

    rows = conn.execute(
        "SELECT captured_at, lat, lon FROM photos"
        " WHERE quest_id = ? AND lat IS NOT NULL ORDER BY captured_at",
        (quest_id,),
    ).fetchall()
    for r in rows:
        points.append((r["captured_at"], r["lat"], r["lon"]))

    if not points:
        return None

    points.sort(key=lambda p: p[0])
    _, lat, lon = points[len(points) // 2]
    return lat, lon


@router.post("/quests/{quest_id}/place", response_model=QuestPlaceResponse)
def place_quest_orphans(
    quest_id: int,
    body: QuestPlaceBody,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> QuestPlaceResponse:
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    if body.lat is not None and body.lon is not None:
        lat, lon = body.lat, body.lon
    else:
        point = _median_point(conn, quest_id)
        if point is None:
            raise HTTPException(
                status_code=422,
                detail="No GPS reference points for this quest — provide lat/lon explicitly",
            )
        lat, lon = point

    result = conn.execute(
        "UPDATE photos SET lat = ?, lon = ?, is_orphan = 0 WHERE quest_id = ? AND is_orphan = 1",
        (lat, lon, quest_id),
    )
    conn.execute(
        """UPDATE quests SET
            bbox_lat_min = (SELECT MIN(lat) FROM photos WHERE quest_id = ? AND lat IS NOT NULL),
            bbox_lat_max = (SELECT MAX(lat) FROM photos WHERE quest_id = ? AND lat IS NOT NULL),
            bbox_lon_min = (SELECT MIN(lon) FROM photos WHERE quest_id = ? AND lon IS NOT NULL),
            bbox_lon_max = (SELECT MAX(lon) FROM photos WHERE quest_id = ? AND lon IS NOT NULL)
        WHERE id = ?""",
        (quest_id, quest_id, quest_id, quest_id, quest_id),
    )
    conn.commit()
    return QuestPlaceResponse(placed=result.rowcount, lat=lat, lon=lon)


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


def _build_gpx(
    quest_name: str, segments: dict[int, list[tuple[float, float, float | None, str | None]]]
) -> bytes:
    root = ET.Element(
        "gpx",
        attrib={
            "version": "1.1",
            "creator": "Stamped",
            "xmlns": "http://www.topografix.com/GPX/1/1",
        },
    )
    meta = ET.SubElement(root, "metadata")
    ET.SubElement(meta, "name").text = quest_name
    for pts in segments.values():
        trk = ET.SubElement(root, "trk")
        seg = ET.SubElement(trk, "trkseg")
        for lat, lon, ele, time in pts:
            trkpt = ET.SubElement(seg, "trkpt", attrib={"lat": str(lat), "lon": str(lon)})
            if ele is not None:
                ET.SubElement(trkpt, "ele").text = str(ele)
            if time is not None:
                ET.SubElement(trkpt, "time").text = time
    return ET.tostring(root, encoding="unicode", xml_declaration=False).encode()


@router.get("/quests/{quest_id}/gpx")
def get_quest_gpx(
    quest_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> Response:
    quest = conn.execute(
        "SELECT id, name, auto_name FROM quests WHERE id = ?", (quest_id,)
    ).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    gpx_files = conn.execute(
        "SELECT id, file_path FROM gpx_files WHERE quest_id = ? ORDER BY id",
        (quest_id,),
    ).fetchall()
    if not gpx_files:
        raise HTTPException(status_code=404, detail="No GPX file for this quest")

    quest_name: str = quest["name"] or quest["auto_name"]
    filename = f"{quest_name.replace(' ', '_')}.gpx"

    if len(gpx_files) == 1:
        import os

        path = gpx_files[0]["file_path"]
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="GPX file not found on disk")
        return FileResponse(
            path,
            media_type="application/gpx+xml",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    rows = conn.execute(
        "SELECT t.gpx_file_id, t.lat, t.lon, t.alt, t.recorded_at"
        " FROM gpx_trackpoints t"
        " JOIN gpx_files f ON f.id = t.gpx_file_id"
        " WHERE f.quest_id = ? ORDER BY t.gpx_file_id, t.recorded_at",
        (quest_id,),
    ).fetchall()
    segments: dict[int, list[tuple[float, float, float | None, str | None]]] = {}
    for r in rows:
        fid = r["gpx_file_id"]
        if fid not in segments:
            segments[fid] = []
        segments[fid].append((r["lat"], r["lon"], r["alt"], r["recorded_at"]))

    body = _build_gpx(quest_name, segments)
    return Response(
        content=b'<?xml version="1.0" encoding="UTF-8"?>\n' + body,
        media_type="application/gpx+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ElevationPoint(BaseModel):
    d: float
    alt: float
    t: str


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@router.get("/quests/{quest_id}/elevation", response_model=list[ElevationPoint])
def get_quest_elevation(
    quest_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> list[ElevationPoint]:
    quest = conn.execute("SELECT id FROM quests WHERE id = ?", (quest_id,)).fetchone()
    if quest is None:
        raise HTTPException(status_code=404, detail="Quest not found")

    rows = conn.execute(
        "SELECT t.lat, t.lon, t.alt, t.recorded_at"
        " FROM gpx_trackpoints t"
        " JOIN gpx_files f ON f.id = t.gpx_file_id"
        " WHERE f.quest_id = ? AND t.alt IS NOT NULL"
        " ORDER BY t.recorded_at",
        (quest_id,),
    ).fetchall()

    if not rows:
        return []

    offset = timedelta(hours=settings.camera_utc_offset_hours)

    def _to_local(recorded_at: str) -> str:
        dt = datetime.strptime(recorded_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        return (dt + offset).strftime("%Y-%m-%dT%H:%M:%SZ")

    points: list[ElevationPoint] = []
    cumulative = 0.0
    prev = rows[0]
    points.append(ElevationPoint(d=0.0, alt=prev["alt"], t=_to_local(prev["recorded_at"])))

    for row in rows[1:]:
        cumulative += _haversine(prev["lat"], prev["lon"], row["lat"], row["lon"])
        points.append(
            ElevationPoint(d=round(cumulative, 1), alt=row["alt"], t=_to_local(row["recorded_at"]))
        )
        prev = row

    return points


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
