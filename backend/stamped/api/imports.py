import asyncio
import logging
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from stamped.core.config import settings
from stamped.core.db import get_connection, get_db
from stamped.core.events import bus
from stamped.services.elevation_service import enrich_elevation
from stamped.services.gpx_service import import_gpx_directory
from stamped.services.import_service import import_directory, interpolate_gps_from_trackpoints
from stamped.services.quest_service import cluster_quests
from stamped.services.thumb_service import process_pending_thumbs

logger = logging.getLogger(__name__)

router = APIRouter()

_jobs: dict[str, "JobState"] = {}


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class JobState:
    job_id: str
    status: str = "running"
    phase: str = "starting"
    progress: float = 0.0
    indexed: int = 0
    total: int = 0
    errors: int = 0
    started_at: str = field(default_factory=_now)
    finished_at: str | None = None


# ── Pydantic schemas ──────────────────────────────────────────────────────────


class ImportRequest(BaseModel):
    path: str


class ImportResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    phase: str
    progress: float
    indexed: int
    total: int
    errors: int
    started_at: str
    finished_at: str | None


class ReindexRequest(BaseModel):
    confirm: bool = False


# ── Pipeline ──────────────────────────────────────────────────────────────────


def _update_system_state(conn: sqlite3.Connection, kv: dict[str, Any]) -> None:
    conn.executemany(
        "INSERT OR REPLACE INTO system_state (key, value, updated_at)"
        " VALUES (?, ?, datetime('now'))",
        [(k, str(v)) for k, v in kv.items()],
    )


def _run_pipeline(
    job: JobState,
    path: Path,
    loop: asyncio.AbstractEventLoop,
) -> None:
    def publish(phase: str, progress: float) -> None:
        job.phase = phase
        job.progress = progress
        loop.call_soon_threadsafe(
            bus.publish,
            "import_progress",
            {
                "job_id": job.job_id,
                "phase": phase,
                "progress": progress,
                "indexed": job.indexed,
                "total": job.total,
            },
        )

    try:
        with get_connection() as conn:
            publish("import", 0.1)
            photo_result = import_directory(path, conn)
            job.indexed = photo_result.indexed
            job.errors += photo_result.errors

            publish("gpx", 0.3)
            gpx_result = import_gpx_directory(path, conn)
            job.errors += gpx_result.errors

            publish("clustering", 0.5)
            cluster_quests(conn)

            publish("interpolation", 0.7)
            interpolate_gps_from_trackpoints(
                conn, utc_offset_hours=settings.camera_utc_offset_hours
            )

            publish("elevation", 0.85)
            enrich_elevation(conn)

            publish("thumbnails", 0.9)
            thumbs_done = thumbs_failed = 0
            while True:
                result = process_pending_thumbs(conn)
                thumbs_done += result.done
                thumbs_failed += result.failed
                if result.done == 0:
                    break

            photos_total = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
            orphans = conn.execute("SELECT COUNT(*) FROM photos WHERE is_orphan = 1").fetchone()[0]
            gpx_count = conn.execute("SELECT COUNT(*) FROM gpx_files").fetchone()[0]
            quests_count = conn.execute("SELECT COUNT(*) FROM quests").fetchone()[0]

            _update_system_state(
                conn,
                {
                    "photos_total": photos_total,
                    "orphans_count": orphans,
                    "gpx_files": gpx_count,
                    "quests": quests_count,
                    "thumbs_done": thumbs_done,
                    "thumbs_pending": thumbs_failed,
                    "last_index_at": _now(),
                },
            )
            conn.commit()

            job.total = photos_total
            job.status = "done"
            job.finished_at = _now()
            publish("done", 1.0)

    except Exception:
        logger.exception("Pipeline failed for job %s", job.job_id)
        job.status = "error"
        job.finished_at = _now()
        loop.call_soon_threadsafe(bus.publish, "import_error", {"job_id": job.job_id})


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/import", response_model=ImportResponse, status_code=202)
async def start_import(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
) -> ImportResponse:
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {request.path}")

    job_id = str(uuid.uuid4())
    job = JobState(job_id=job_id)
    _jobs[job_id] = job

    loop = asyncio.get_event_loop()
    background_tasks.add_task(_run_pipeline, job, path, loop)

    return ImportResponse(job_id=job_id, status="started")


@router.get("/import/{job_id}", response_model=JobStatusResponse)
async def get_import_status(job_id: str) -> JobStatusResponse:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        phase=job.phase,
        progress=job.progress,
        indexed=job.indexed,
        total=job.total,
        errors=job.errors,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.post("/reindex")
def reindex(
    request: ReindexRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> dict[str, str]:
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required: set confirm=true")
    conn.execute("DELETE FROM photos")
    conn.execute("DELETE FROM quests")
    conn.execute("DELETE FROM gpx_files")
    conn.execute("DELETE FROM geocode_cache")
    conn.execute("DELETE FROM system_state")
    conn.commit()
    _jobs.clear()
    return {"status": "cleared"}
