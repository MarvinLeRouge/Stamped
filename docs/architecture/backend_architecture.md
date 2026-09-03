[🇫🇷 Version française](backend_architecture.fr.md) | 🇬🇧 English version

---

# Backend Architecture - Stamped

## Overview

The backend is a FastAPI application (`backend/stamped/`) serving a REST API on `127.0.0.1:8421`. It has no authentication layer and is designed to run on a single trusted machine.

## Layout

```
backend/stamped/
├── api/           # FastAPI routers - request parsing, Pydantic response models, orchestration
│   ├── photos.py
│   ├── quests.py
│   ├── imports.py
│   ├── search.py
│   ├── status.py
│   ├── tiles.py
│   └── main.py    # app factory, router registration, lifespan (init_db at startup)
├── services/      # Business logic - pure Python, no FastAPI imports, no HTTP concepts
│   ├── import_service.py
│   ├── quest_service.py
│   ├── thumb_service.py
│   ├── gpx_service.py
│   └── elevation_service.py
├── workers/       # CPU-bound, stateless functions - receive data, return data, no DB access
│   ├── exif_worker.py
│   ├── gpx_worker.py
│   ├── thumb_worker.py
│   └── elevation_worker.py
├── core/          # Cross-cutting concerns
│   ├── db.py      # sqlite3 connection, migration runner
│   ├── config.py  # pydantic-settings, STAMPED_* env vars
│   ├── events.py  # SSE event bus
│   └── fs.py      # single source of truth for data/ path construction
└── cli.py         # `stamped start` / `stamped index` / `stamped status`
```

## Tech stack

Python 3.12+, FastAPI, uvicorn, `sqlite3` (standard library), Pydantic. EXIF via `exifread` and `piexif`, GPX via `gpxpy`, thumbnails via Pillow, geocoding via `geopy` (Nominatim), elevation lookups via `httpx` against OpenTopoData. SSE served with `sse-starlette`. `sqlmodel` is listed in `pyproject.toml` but not currently used anywhere in the codebase.

## Data access

Stamped talks to SQLite directly through the standard library `sqlite3` module (parameterized queries, `sqlite3.Row` row factory) - there is no ORM. Response shapes are declared as Pydantic `BaseModel` classes next to each router (e.g. `PhotoSummary` in `api/photos.py`), decoupled from the raw SQL result. Table schemas live entirely in `migrations/*.sql`.

## Migrations

Schema changes are versioned SQL scripts (`migrations/001_init.sql`, `migrations/002_deleted_photos.sql`, ...), applied once each in filename order by `core/db.py::init_db()` at process startup, tracked in a `schema_migrations` table. See [ADR 0009](../adr/0009-versioned-sql-migrations-no-alembic.md) for why this is used instead of an ORM migration tool.

## Import pipeline

`POST /api/import` triggers `services/import_service.py`, which runs in phases:

> **Note:** the `stamped index <path>` CLI command is currently a stub (`backend/stamped/cli.py`) and does not call the import pipeline - see [docs/operations.md](../operations.md). The only working way to start an import today is `POST /api/import`.

1. **EXIF indexing** - `workers/exif_worker.py` extracts capture time, GPS, camera make/model from each JPEG; results are written immediately so the map is usable before later phases finish.
2. **GPX parsing + quest clustering** - `workers/gpx_worker.py` parses trackpoints; `services/quest_service.py` groups photos into quests by temporal gaps (see [ADR 0006](../adr/0006-quest-detection-temporal-clustering.md)) and matches GPX files to quests.
3. **GPS interpolation + elevation enrichment** - photos without EXIF GPS are interpolated from surrounding GPX trackpoints (never across two different GPX files, see [ADR 0014](../adr/0014-gps-interpolation-single-gpx-file-boundary.md)); elevation is fetched from OpenTopoData (see [ADR 0004](../adr/0004-elevation-via-opentopodata-no-local-dem.md)).
4. **Thumbnail generation** - `workers/thumb_worker.py` runs last, in the background, lowest priority.

Camera clock vs. GPX UTC time is reconciled via a configurable offset applied consistently across interpolation, GPX-to-quest matching, and the elevation profile endpoint - see [ADR 0013](../adr/0013-camera-utc-offset-reconciliation.md).

CPU-bound steps run in a `concurrent.futures.ProcessPoolExecutor`; progress is pushed to the frontend over Server-Sent Events (`core/events.py`, `GET /api/events`) rather than polling - see [ADR 0007](../adr/0007-sse-for-realtime-progress.md).

## Static tile and thumbnail serving

`api/tiles.py` proxies OSM-compatible tile servers (multiple layers: OSM, topo, satellite) with a per-layer filesystem cache under `data/tiles/{layer}/` (see [ADR 0015](../adr/0015-osm-layer-alternatives-per-layer-cache.md)). Thumbnails are served from `data/thumbs/{hash[:2]}/{hash}.jpg` via `api/photos.py`, generated on demand if missing rather than stored in the database (see [ADR 0002](../adr/0002-images-never-stored-in-database.md)).

## Full endpoint list

See [docs/api/api_endpoints.md](../api/api_endpoints.md).
