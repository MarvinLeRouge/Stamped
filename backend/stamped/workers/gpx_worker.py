import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import gpxpy
import gpxpy.gpx

logger = logging.getLogger(__name__)


@dataclass
class TrackpointData:
    recorded_at: str
    lat: float
    lon: float
    alt: float | None


@dataclass
class GpxData:
    recorded_at_start: str | None
    recorded_at_end: str | None
    point_count: int
    total_distance_m: float
    elevation_gain_m: float
    trackpoints: list[TrackpointData] = field(default_factory=list)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_gpx(file_path: Path) -> GpxData | None:
    """Parse a GPX file and return structured data. Pure — no side effects."""
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as f:
            gpx = gpxpy.parse(f)
    except Exception:
        logger.warning("Cannot parse GPX %s", file_path, exc_info=True)
        return None

    trackpoints: list[TrackpointData] = []

    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                if pt.time is None:
                    continue
                trackpoints.append(
                    TrackpointData(
                        recorded_at=_iso(pt.time) or "",
                        lat=pt.latitude,
                        lon=pt.longitude,
                        alt=pt.elevation,
                    )
                )

    if not trackpoints:
        logger.info("No timed trackpoints in %s", file_path)
        return None

    total_distance = gpx.length_2d() or 0.0
    uphill, _ = gpx.get_uphill_downhill()
    elevation_gain = uphill or 0.0

    return GpxData(
        recorded_at_start=trackpoints[0].recorded_at,
        recorded_at_end=trackpoints[-1].recorded_at,
        point_count=len(trackpoints),
        total_distance_m=total_distance,
        elevation_gain_m=elevation_gain,
        trackpoints=trackpoints,
    )
