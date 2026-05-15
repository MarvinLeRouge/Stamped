# Stamped — Architecture

> Public technical reference. Summarizes key design decisions.

---

## Overview

Stamped is a two-process local web application:

- **Backend** — FastAPI (Python) on `localhost:8421`. Handles file indexing, EXIF extraction, GPX parsing, quest detection, thumbnail generation, and serves the REST API.
- **Frontend** — Vue 3 + Vite SPA. Served by the backend in production, Vite dev server in development. Displays the Leaflet map, quest list, storyline, and import dashboard.

Both processes communicate via a REST API. Real-time progress (import, thumbnail generation) is delivered via Server-Sent Events.

---

## Key design decisions

**Local-first.** All data stays on the machine. Three optional outbound calls exist (OSM tiles, OpenTopoData elevation, Nominatim geocoding) — all results are cached locally and the app works offline after first use.

**Images never in the database.** Original photos are read-only and never moved. Thumbnails live in a filesystem mirror (`data/thumbs/`). The SQLite database stores only paths and metadata.

**Quests auto-detected.** Photos are grouped into quests by detecting temporal gaps > 6 hours. No manual tagging required.

**Async import pipeline.** Import runs in four phases: EXIF indexing (immediate) → quest clustering (fast) → GPS interpolation + elevation enrichment (async) → thumbnail generation (background, lowest priority). The map is usable before thumbnails are ready.

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, FastAPI, SQLModel, SQLite |
| Workers | `concurrent.futures.ProcessPoolExecutor` |
| EXIF | `exifread`, `piexif` |
| GPX | `gpxpy` |
| Thumbnails | Pillow |
| Elevation | OpenTopoData API (Mapzen model) |
| Geocoding | Nominatim via `geopy` |
| Frontend | Vue 3, Vite, TypeScript |
| Map | Leaflet, `@vue-leaflet/vue-leaflet`, Leaflet.markercluster |
| State | Pinia |

---

## Project structure

```
stamped/
├── backend/
│   ├── stamped/
│   │   ├── api/          # FastAPI routes
│   │   ├── workers/      # CPU-bound subprocesses
│   │   ├── models/       # SQLModel + Pydantic schemas
│   │   ├── services/     # business logic
│   │   └── core/         # db, config, events, fs
│   └── tests/
├── frontend/
│   └── src/
├── data/                 # runtime, gitignored
└── migrations/           # versioned SQL scripts
```

---

## API

Base URL: `http://localhost:8421/api`

Main resources: `/photos`, `/quests`, `/import`, `/status`, `/search/geocode`  
OSM tile proxy: `/tiles/{z}/{x}/{y}.png`  
Real-time events: `/events` (SSE)
