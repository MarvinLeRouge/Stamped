[🇫🇷 Version française](README.fr.md) | 🇬🇧 English version

---

# Stamped

> *A local-first web app that turns your photo library and GPX tracks into a personal conquest map — fully private, nothing leaves your machine.*

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
[![CI](https://github.com/MarvinLeRouge/Stamped/actions/workflows/ci.yml/badge.svg)](https://github.com/MarvinLeRouge/Stamped/actions)
[![codecov backend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=backend&label=backend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
[![codecov frontend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=frontend&label=frontend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
![License](https://img.shields.io/github/license/MarvinLeRouge/Stamped?cacheSeconds=3600)

---

## 💡 Concept

Standard photo apps ask you to tag, organize and describe. Stamped doesn't. Point it at a folder, and it reads your EXIF data and GPX tracks, detects your outings automatically, places every photo on a map, and shows you the extent of your documented territory at a glance.

Each geotagged photo is evidence of presence. Stamped treats your collection as a geographic record, not an album.

---

## 📊 Key figures

| Metric | Value |
|---|---|
| Backend tests | **208 passing** |
| Frontend tests | **146 passing** |
| API endpoints | **19** |
| Backend coverage | **99%** |
| Frontend coverage | **97%** |
| Import pipeline stages | **6** (EXIF · GPX · quests · GPS interpolation · elevation · thumbnails) |

---

## 📸 Screenshots

### All quests

[![All quests](docs/screenshots/quests-all.png)](docs/screenshots/quests-all.png)

### Quest view — elevation profile collapsed

[![Quest view — elevation profile collapsed](docs/screenshots/quest-without-altitude.png)](docs/screenshots/quest-without-altitude.png)

### Photo marker hover

[![Photo marker hover](docs/screenshots/quest-hover-marker.png)](docs/screenshots/quest-hover-marker.png)

### Cluster hover — elevation sync

[![Cluster hover — elevation sync](docs/screenshots/quest-hover-cluster.png)](docs/screenshots/quest-hover-cluster.png)

### Opened cluster hover

[![Opened cluster hover](docs/screenshots/quest-hover-opened-cluster.png)](docs/screenshots/quest-hover-opened-cluster.png)

### Alternate OSM layer

[![Alternate OSM layer](docs/screenshots/quest-osm-alternate.png)](docs/screenshots/quest-osm-alternate.png)

---

## ✨ Features

- **Conquest map** — all geotagged photos on an OSM map, clustered by zoom level; filter by quest, date range or bounding box
- **Quest detection** — outings auto-detected by temporal clustering (configurable gap); quests renameable
- **Storyline** — per-quest scrollable photo list with timestamps, thumbnails and inline actions
- **GPX support** — import tracks, display per-file polylines, interpolate position for photos without GPS coordinates, export quest GPX
- **Orphan management** — photos without coordinates placed individually on the map (click-to-place) or in bulk via chronological median of quest GPS points
- **Photo deletion** — removes DB record and generated thumbnail; original file is never touched; deleted hashes blocklisted to prevent re-indexing
- **Offline-first** — OSM tiles cached locally after first fetch; elevation data enriched once at import; full offline operation after initial run
- **Private by design** — no account, no cloud sync, no analytics

---

## 🏗️ Architecture

```
backend/
├── stamped/
│   ├── api/           # FastAPI routes — thin, no business logic
│   ├── services/      # Business logic (import, quests, thumbnails, elevation, GPX)
│   ├── workers/       # CPU-bound tasks (EXIF extraction, GPX parsing, thumb generation, elevation API)
│   └── core/          # db.py · config.py · events.py (SSE) · fs.py
├── tests/             # Mirrors source structure
migrations/            # Versioned SQL scripts (no ORM migration tool)

frontend/
└── src/
    ├── components/    # MapView · QuestList · QuestStoryline · PhotoLightbox · StatusDashboard
    └── stores/        # photos · quests · lightbox · placement · status
```

### Database schema (SQLite)

| Table | Role |
|---|---|
| `photos` | All imported photos — EXIF metadata, GPS, thumb status, orphan flag |
| `quests` | Auto-detected outings — name, bbox, photo count |
| `gpx_files` | Imported GPX files linked to quests |
| `gpx_trackpoints` | All track points with timestamps |
| `deleted_photos` | SHA-256 blocklist — prevents re-indexing deleted photos |
| `geocode_cache` | Nominatim reverse geocoding cache |
| `system_state` | Import metadata (last index date) |

---

## 🧠 Design decisions

### Live COUNT vs. cached counter for orphan stats

`GET /api/status` queries `SELECT COUNT(*) FROM photos WHERE is_orphan = 1` on every call rather than reading a cached value from `system_state`. The `idx_photos_orphan` index makes this O(orphan count) — sub-millisecond at any realistic personal collection size. A cached counter would require consistent updates across four distinct endpoints (`PATCH /photos/{id}`, `DELETE /photos/{id}`, `POST /quests/{id}/place`, import pipeline). Each missing update is a silent data drift. We discovered this in practice: the cached counter went stale the moment manual placement was added. On SQLite with indexes, live aggregates are more reliable than application-level caches unless measurements show otherwise.

### Photo deletion — DB only, original files untouched

`DELETE /api/photos/{id}` removes the database record and the generated thumbnail, then inserts the file's SHA-256 hash into `deleted_photos`. The original file is never modified or deleted. The SHA-256 is already computed at import for deduplication — the blocklist check adds zero overhead to the import pipeline. Without the blocklist, `stamped index` on the same folder would re-import the deleted photo on the next run.

### Chronological median for bulk orphan placement

`POST /api/quests/{id}/place` uses the chronological median GPS point (trackpoints + geolocated photos, sorted by timestamp, middle element) rather than the geometric centroid. On a linear out-and-back route, the arithmetic mean of all coordinates would fall somewhere in the middle of the trail — which the median does too, but anchored to actual time spent rather than geometric space. On a loop, the mean can fall off the trail entirely. The placed position is a starting point; the user can override it with explicit coordinates or refine photo by photo afterward.

---

## 📡 API

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/status` | System status — photo count, orphan count, last import |
| `GET` | `/api/quests` | All quests ordered by date |
| `PATCH` | `/api/quests/{id}` | Rename a quest |
| `GET` | `/api/quests/{id}/photos` | Chronological photo list for a quest |
| `GET` | `/api/quests/{id}/trackpoints` | GPX segments grouped by file |
| `GET` | `/api/quests/{id}/gpx` | Download quest GPX (merged if multiple files) |
| `POST` | `/api/quests/{id}/place` | Place all orphan photos of a quest at median GPS point |
| `GET` | `/api/photos` | Photo list with bbox / date / quest / orphan filters |
| `PATCH` | `/api/photos/{id}` | Set GPS coordinates, clear orphan flag |
| `DELETE` | `/api/photos/{id}` | Remove from DB + delete thumbnail, blocklist hash |
| `GET` | `/api/photos/{id}/thumb` | Serve generated thumbnail (202 if pending) |
| `GET` | `/api/photos/{id}/original` | Serve original file |
| `POST` | `/api/photos/{id}/thumb/priority` | Bump thumbnail to priority queue |
| `POST` | `/api/import` | Start import pipeline, returns job ID |
| `GET` | `/api/import/{job_id}` | Import job status and progress |
| `POST` | `/api/reindex` | Clear and re-import everything |
| `GET` | `/api/search/geocode` | Nominatim geocoding proxy (cached) |
| `GET` | `/api/tiles/{z}/{x}/{y}.png` | OSM tile proxy (filesystem cache) |
| `GET` | `/api/events` | SSE stream for import progress |

---

## 🧪 Testing

### Backend — pytest

```bash
make test-backend
# or
python -m pytest backend/tests/ -v --cov=backend/stamped
```

- Isolated SQLite DB per test (`tmp_path` fixture, no shared state)
- Full import pipeline tested end-to-end with real JPEG and GPX fixtures
- Edge cases: GPS interpolation across file boundaries, cross-activity deduplication, elevation API failure, thumbnail orientation

### Frontend — Vitest

```bash
make test-frontend
# or
cd frontend && npm run test:unit -- --coverage
```

- JSDOM environment, Vue Test Utils
- Pinia stores tested in isolation
- Component tests cover: map interactions, placement mode, lightbox, storyline rename/delete/place flow

### Run everything

```bash
make test
```

---

## ⚙️ CI

[`ci.yml`](.github/workflows/ci.yml) — triggers on push and pull request:

1. **Lint** — ruff, mypy (backend) · ESLint, Prettier, vue-tsc (frontend)
2. **Backend tests** — pytest with coverage, uploaded to Codecov (`backend` flag)
3. **Frontend tests** — Vitest with coverage, uploaded to Codecov (`frontend` flag)
4. **Pre-push hook** — vue-tsc type-check runs locally before any push

---

## 🚀 Getting started

**Prerequisites** — Python 3.12+, Node.js 18+

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git && cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && npm run build && cd ..

# Start (opens browser automatically at http://localhost:8421)
stamped start

# Import a folder of photos and GPX files
stamped index ~/Photos/2024/hiking
```

Optional — camera UTC offset (for GPS interpolation accuracy):

```bash
# .env
STAMPED_CAMERA_UTC_OFFSET_HOURS=2   # e.g. CEST
```

---

## 🔒 Privacy

Stamped makes three optional outbound network calls:

| Call | When | Cached |
|---|---|---|
| OSM tiles | First map view of a zone | Locally, forever |
| OpenTopoData | At import only | In SQLite |
| Nominatim | Quest geocoding | In SQLite |

After the first import of a geographic area, Stamped works entirely offline.

---

## 🗺️ Roadmap

### ✅ v1 — Delivered

- [x] **Phase 0** — Repository, tooling, CI
- [x] **Phase 1** — Backend skeleton (FastAPI, SQLite, SSE, config)
- [x] **Phase 2** — Import pipeline (EXIF, GPX, quest clustering, GPS interpolation, elevation, thumbnails)
- [x] **Phase 3** — Thumbnail generation (Pillow, EXIF orientation, priority queue)
- [x] **Phase 4** — Map & frontend (Leaflet, clustering, filters, lightbox, GPX polylines)
- [x] **Phase 5** — Storyline (per-quest photo list, quest renaming, GPX export)
- [x] **Phase 6** — Orphan management (manual placement, bulk placement, photo deletion, deleted-hash blocklist)
- [x] **Phase 7** — Desktop layout (CSS Grid, font scale, boilerplate cleanup)

### ✅ v2 — Delivered

- [x] Synchronized storyline ↔ map — hover on a photo highlights the map marker, and vice versa
- [x] "Photos without quest" view — photos with `quest_id = NULL`, with placement and deletion actions
- [x] Global photo browser — all photos with orphan status filter
- [x] Alternative OSM layers (topo, satellite) — with filesystem tile cache per layer
- [x] Elevation profile — collapsible panel below the map, SVG chart with distance axis, synced with storyline hover

### 🔜 v3 — Planned

- [ ] **Quest macro timeline** — full-width animated view replacing the content area; quests positioned by chronological midpoint (day precision); fixed-width blocks stacked vertically by density (oldest on top); collapsed "N quests" blocks when capacity exceeded; mouse-wheel zoom; click returns to normal view
- [ ] Folder watch — automatic import on file change
- [ ] RAW image support
- [ ] Export (JSON, filtered GPX)
- [ ] Activity type tagging
- [ ] Dark theme
- [ ] Keyboard shortcuts

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| Backend | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square) ![Python](https://img.shields.io/badge/Python_3.12-3776AB?logo=python&logoColor=white&style=flat-square) |
| Database | ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white&style=flat-square) versioned SQL migrations |
| Frontend | ![Vue.js](https://img.shields.io/badge/Vue.js_3-4FC08D?logo=vuedotjs&logoColor=white&style=flat-square) ![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white&style=flat-square) |
| Map | ![Leaflet](https://img.shields.io/badge/Leaflet-199900?logo=leaflet&logoColor=white&style=flat-square) + Leaflet.markercluster |
| State | ![Pinia](https://img.shields.io/badge/Pinia-FFD859?logo=pinia&logoColor=black&style=flat-square) |
| EXIF | Pillow |
| Backend testing | ![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white&style=flat-square) — 208 tests, 99% coverage |
| Frontend testing | ![Vitest](https://img.shields.io/badge/Vitest-6E9F18?logo=vitest&logoColor=white&style=flat-square) + Vue Test Utils — 146 tests, 97% coverage |
| Linting | ruff · mypy · ESLint · Prettier · vue-tsc |
| CI | ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white&style=flat-square) ![Codecov](https://img.shields.io/badge/Codecov-F01F7A?logo=codecov&logoColor=white&style=flat-square) |

---

## 📋 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

*Solo project · Local-first · No tracking · No ads*
