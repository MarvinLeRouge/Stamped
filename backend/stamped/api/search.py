import logging
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from stamped.core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class GeocodeResult(BaseModel):
    display_name: str
    lat: float
    lon: float
    bbox_lat_min: float | None
    bbox_lat_max: float | None
    bbox_lon_min: float | None
    bbox_lon_max: float | None


def _fetch_nominatim(q: str) -> list[GeocodeResult]:
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="stamped-local/1.0")
    try:
        locations = geolocator.geocode(q, exactly_one=False, limit=5)
    except Exception:
        logger.warning("Nominatim geocode failed for %r", q, exc_info=True)
        return []

    if not locations:
        return []

    results = []
    for loc in locations:
        raw = getattr(loc, "raw", {})
        bb = raw.get("boundingbox")
        results.append(
            GeocodeResult(
                display_name=loc.address,
                lat=loc.latitude,
                lon=loc.longitude,
                bbox_lat_min=float(bb[0]) if bb else None,
                bbox_lat_max=float(bb[1]) if bb else None,
                bbox_lon_min=float(bb[2]) if bb else None,
                bbox_lon_max=float(bb[3]) if bb else None,
            )
        )
    return results


def _cache_get(conn: sqlite3.Connection, q: str) -> list[GeocodeResult] | None:
    rows = conn.execute(
        "SELECT place_name, lat_rounded, lon_rounded FROM geocode_cache"
        " WHERE place_name LIKE ? LIMIT 5",
        (f"%{q}%",),
    ).fetchall()
    if not rows:
        return None
    return [
        GeocodeResult(
            display_name=r["place_name"],
            lat=r["lat_rounded"],
            lon=r["lon_rounded"],
            bbox_lat_min=None,
            bbox_lat_max=None,
            bbox_lon_min=None,
            bbox_lon_max=None,
        )
        for r in rows
    ]


def _cache_put(conn: sqlite3.Connection, results: list[GeocodeResult]) -> None:
    for r in results:
        conn.execute(
            "INSERT OR IGNORE INTO geocode_cache (lat_rounded, lon_rounded, place_name)"
            " VALUES (?, ?, ?)",
            (round(r.lat, 3), round(r.lon, 3), r.display_name),
        )
    conn.commit()


@router.get("/search/geocode", response_model=list[GeocodeResult])
def geocode_search(
    q: Annotated[str, Query(min_length=2)],
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> list[GeocodeResult]:
    cached = _cache_get(conn, q)
    if cached:
        return cached

    results = _fetch_nominatim(q)
    if results:
        _cache_put(conn, results)
    return results
