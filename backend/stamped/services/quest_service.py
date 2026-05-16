import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from stamped.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    quests_created: int
    photos_assigned: int
    gpx_assigned: int


def _parse_iso(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _auto_name(started_at: str) -> str:
    return f"Quest {started_at[:10]}"


def cluster_quests(conn: sqlite3.Connection) -> ClusterResult:
    """
    Re-cluster all timestamped photos into quests using temporal gap detection.

    Groups consecutive photos separated by less than quest_gap_hours into the same
    quest. Existing quests are fully replaced on each call. GPX files whose time
    window overlaps a quest are associated and set has_gpx=1 on that quest.
    """
    conn.execute("UPDATE photos SET quest_id = NULL")
    conn.execute("UPDATE gpx_files SET quest_id = NULL")
    conn.execute("DELETE FROM quests")

    rows = conn.execute(
        "SELECT id, captured_at, lat, lon FROM photos"
        " WHERE captured_at IS NOT NULL ORDER BY captured_at"
    ).fetchall()

    if not rows:
        conn.commit()
        return ClusterResult(quests_created=0, photos_assigned=0, gpx_assigned=0)

    gap_seconds = settings.quest_gap_hours * 3600

    groups: list[list[sqlite3.Row]] = []
    current: list[sqlite3.Row] = [rows[0]]

    for row in rows[1:]:
        delta = (
            _parse_iso(row["captured_at"]) - _parse_iso(current[-1]["captured_at"])
        ).total_seconds()
        if delta > gap_seconds:
            groups.append(current)
            current = [row]
        else:
            current.append(row)
    groups.append(current)

    quests_created = photos_assigned = gpx_assigned = 0

    for group in groups:
        started_at = group[0]["captured_at"]
        ended_at = group[-1]["captured_at"]

        lats = [r["lat"] for r in group if r["lat"] is not None]
        lons = [r["lon"] for r in group if r["lon"] is not None]

        cursor = conn.execute(
            """
            INSERT INTO quests
                (auto_name, started_at, ended_at, photo_count,
                 bbox_lat_min, bbox_lat_max, bbox_lon_min, bbox_lon_max)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _auto_name(started_at),
                started_at,
                ended_at,
                len(group),
                min(lats) if lats else None,
                max(lats) if lats else None,
                min(lons) if lons else None,
                max(lons) if lons else None,
            ),
        )
        quest_id = cursor.lastrowid
        quests_created += 1

        conn.executemany(
            "UPDATE photos SET quest_id = ? WHERE id = ?",
            [(quest_id, r["id"]) for r in group],
        )
        photos_assigned += len(group)

        gpx_rows = conn.execute(
            "SELECT id FROM gpx_files WHERE recorded_at_start <= ? AND recorded_at_end >= ?",
            (ended_at, started_at),
        ).fetchall()

        if gpx_rows:
            conn.executemany(
                "UPDATE gpx_files SET quest_id = ? WHERE id = ?",
                [(quest_id, r["id"]) for r in gpx_rows],
            )
            conn.execute("UPDATE quests SET has_gpx = 1 WHERE id = ?", (quest_id,))
            gpx_assigned += len(gpx_rows)

    conn.commit()
    return ClusterResult(
        quests_created=quests_created,
        photos_assigned=photos_assigned,
        gpx_assigned=gpx_assigned,
    )
