import logging
import sqlite3
from dataclasses import dataclass

from stamped.workers.elevation_worker import fetch_elevation

logger = logging.getLogger(__name__)


@dataclass
class ElevationResult:
    enriched: int
    failed: int


def enrich_elevation(conn: sqlite3.Connection) -> ElevationResult:
    """
    Fetch and store altitude for all photos that have GPS coordinates but no altitude.

    On success: sets alt (metres) and alt_src='api'.
    On network/API failure: sets alt_src='none', alt remains NULL.
    Photos already enriched (alt IS NOT NULL) or without GPS are skipped.
    """
    rows = conn.execute(
        "SELECT id, lat, lon FROM photos WHERE lat IS NOT NULL AND alt IS NULL"
    ).fetchall()

    if not rows:
        return ElevationResult(enriched=0, failed=0)

    points = [(r["lat"], r["lon"]) for r in rows]
    altitudes = fetch_elevation(points)

    enriched = failed = 0

    for row, alt in zip(rows, altitudes, strict=True):
        if alt is not None:
            conn.execute(
                "UPDATE photos SET alt = ?, alt_src = 'api' WHERE id = ?",
                (alt, row["id"]),
            )
            enriched += 1
        else:
            conn.execute(
                "UPDATE photos SET alt_src = 'none' WHERE id = ?",
                (row["id"],),
            )
            failed += 1

    conn.commit()
    return ElevationResult(enriched=enriched, failed=failed)
