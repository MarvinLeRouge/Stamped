[🇫🇷 Version française](operations.fr.md) | 🇬🇧 English version

---

# Operations - Stamped

## Prerequisites

Python 3.12+, Node.js 18+.

## Install

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git && cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && npm run build && cd ..
```

## Start

```bash
stamped start
```

Opens `http://localhost:8421` in the browser automatically (`--no-browser` to skip). If `frontend/dist/` is missing, `stamped start` builds it first via `npm run build`. Binds to `127.0.0.1` only, see [SECURITY.md](../SECURITY.md).

## Import photos and GPX tracks

> **Current state:** the `stamped index <path>` CLI command described in earlier iterations of this project is a stub (`backend/stamped/cli.py`) - it prints a message and does nothing. The only working way to start an import today is the HTTP API, while the server is running. Wiring the CLI command (or removing it) is tracked in the [roadmap](roadmap.md).

With the server running (`stamped start`):

```bash
curl -X POST http://localhost:8421/api/import \
  -H "Content-Type: application/json" \
  -d '{"path": "/absolute/path/to/photos"}'
```

Returns a job ID; poll `GET /api/import/{job_id}` for progress, or watch `GET /api/events` (SSE) for real-time phase updates. See [docs/api/api_endpoints.md](api/api_endpoints.md) for the full request/response shapes.

To wipe and re-import everything: `POST /api/reindex`.

## Check system status

```bash
stamped status
```

Prints photo count, thumbnail progress, orphan count, quest count and GPX file count. Requires the server to be running.

## Configuration

Environment variables (prefix `STAMPED_`), read from `.env` at the repository root or the process environment:

| Variable | Default | Meaning |
|---|---|---|
| `STAMPED_PORT` | `8421` | HTTP port |
| `STAMPED_DATA_DIR` | `data` | Root directory for the SQLite DB, thumbnails and tile cache |
| `STAMPED_QUEST_GAP_HOURS` | `6` | Temporal gap used to split photos into separate quests, see [ADR 0006](adr/0006-quest-detection-temporal-clustering.md) |
| `STAMPED_THUMB_SIZE` | `400` | Generated thumbnail size in pixels |
| `STAMPED_CAMERA_UTC_OFFSET_HOURS` | `0` | Camera clock offset from UTC, see [ADR 0013](adr/0013-camera-utc-offset-reconciliation.md) |

Example `.env`:

```bash
STAMPED_CAMERA_UTC_OFFSET_HOURS=2   # e.g. CEST
```

## Data directory

```
data/
├── stamped.db     # SQLite database
├── thumbs/         # generated thumbnails, gitignored
└── tiles/           # cached map tiles, per layer, gitignored
```

Deleting `data/` resets the app to a blank state; original photos are never touched (they are only ever read, see [ADR 0002](adr/0002-images-never-stored-in-database.md)).

## Network calls

| Call | When | Cached |
|---|---|---|
| OSM tiles | First map view of a zone | Locally, forever |
| OpenTopoData | At import only | In SQLite |
| Nominatim | Quest geocoding | In SQLite |

After the first import of a geographic area, Stamped works entirely offline. See [SECURITY.md](../SECURITY.md) for the full network/attack-surface notes.

## Tests and linting

```bash
make test          # backend + frontend
make test-backend   # pytest
make test-frontend    # vitest
make lint            # ruff, mypy, eslint, prettier check, vue-tsc
make format            # ruff format, eslint --fix, prettier --write
```
