[🇫🇷 Version française](api_endpoints.fr.md) | 🇬🇧 English version

---

# API Reference - Stamped

Base URL: `http://127.0.0.1:8421/api` (SSE endpoint and tile proxy live outside the `/api` prefix for the tile route only, see below).

This is a static, committed reference kept in sync manually. The live interactive docs (Swagger UI) are only reachable once the app is installed and running, at `http://127.0.0.1:8421/docs` - this file exists so the API surface can be reviewed without installing anything.

## Status

### `GET /api/status`

Returns aggregate counters, computed live (not cached, see [ADR 0010](../adr/0010-live-count-vs-cached-orphan-counter.md)).

```json
{
  "photos_total": 0,
  "thumbs_done": 0,
  "thumbs_pending": 0,
  "orphans": 0,
  "unquested": 0,
  "gpx_files": 0,
  "quests": 0,
  "last_index_at": null
}
```

## Quests

### `GET /api/quests`

All quests ordered by `started_at`. Each item:

```json
{
  "id": 1,
  "name": null,
  "auto_name": "2024-08-12",
  "started_at": "2024-08-12T08:00:00Z",
  "ended_at": "2024-08-12T17:00:00Z",
  "photo_count": 42,
  "has_gpx": true,
  "bbox_lat_min": 45.1,
  "bbox_lat_max": 45.4,
  "bbox_lon_min": 6.1,
  "bbox_lon_max": 6.5
}
```

### `PATCH /api/quests/{quest_id}`

Body: `{"name": "New name"}` (or `null`/blank to fall back to `auto_name`). Returns the updated quest (same shape as above). `404` if the quest does not exist.

### `GET /api/quests/{quest_id}/photos`

Chronological photo list for a quest:

```json
[{"id": 1, "lat": 45.2, "lon": 6.3, "captured_at": "2024-08-12T09:00:00Z", "thumb_status": "done", "is_orphan": false}]
```

### `GET /api/quests/{quest_id}/trackpoints`

GPX trackpoints grouped by file, one segment (list of `[lat, lon]` pairs) per GPX file:

```json
[[[45.2, 6.3], [45.21, 6.31]], [[45.3, 6.4]]]
```

### `GET /api/quests/{quest_id}/gpx`

Downloads the quest's GPX track (`application/gpx+xml`). If the quest has a single source GPX file, that file is served as-is; if it has several, they are merged into one generated GPX document. `404` if the quest has no GPX file.

### `POST /api/quests/{quest_id}/place`

Bulk-places all orphan photos of a quest. Body `{}` uses the chronological median GPS point (see [ADR 0012](../adr/0012-chronological-median-orphan-placement.md)); body `{"lat": ..., "lon": ...}` uses explicit coordinates instead.

```json
{"placed": 5, "lat": 45.2, "lon": 6.3}
```

`422` if no GPS reference points exist for the quest and no explicit coordinates were given.

### `GET /api/quests/{quest_id}/elevation`

Elevation profile points along the quest's GPX trackpoints, cumulative distance in meters, timestamps adjusted by `STAMPED_CAMERA_UTC_OFFSET_HOURS` (see [ADR 0013](../adr/0013-camera-utc-offset-reconciliation.md)):

```json
[{"d": 0.0, "alt": 1200.5, "t": "2024-08-12T09:00:00Z"}]
```

## Photos

### `GET /api/photos`

Query parameters (all optional): `lat_min`, `lat_max`, `lon_min`, `lon_max` (bounding box), `date_from`, `date_to`, `quest_id`, `orphan` (bool), `no_quest` (bool), `limit` (1-1000, default 500), `offset`.

```json
[{"id": 1, "lat": 45.2, "lon": 6.3, "captured_at": "2024-08-12T09:00:00Z", "thumb_status": "done", "quest_id": 1, "is_orphan": false}]
```

### `PATCH /api/photos/{photo_id}`

Body: `{"lat": 45.2, "lon": 6.3}`. Sets coordinates and clears the orphan flag. Returns the updated photo. `404` if not found.

### `DELETE /api/photos/{photo_id}`

Removes the DB record, deletes the generated thumbnail file if present, and adds the photo's SHA-256 hash to `deleted_photos` to prevent re-import (see [ADR 0011](../adr/0011-photo-deletion-db-only.md)). The original file is never touched. `204` on success, `404` if not found.

### `GET /api/photos/{photo_id}/thumb`

Serves the generated thumbnail (`image/jpeg`) if ready. Returns `202` with header `X-Thumb-Status` if the thumbnail is still pending.

### `GET /api/photos/{photo_id}/original`

Serves the original photo file (`image/jpeg`), read directly from its path on disk.

### `POST /api/photos/{photo_id}/thumb/priority`

Queues the photo's thumbnail generation ahead of the background queue. Returns `{"status": "queued"}`.

## Import

### `POST /api/import`

> See [docs/operations.md](../operations.md) - this is currently the only working way to trigger an import; the `stamped index` CLI command is a stub.

Body: `{"path": "/absolute/path/to/photos"}`. `400` if the path does not exist. Starts the import pipeline as a background task and returns immediately (`202`):

```json
{"job_id": "b3f1...", "status": "started"}
```

### `GET /api/import/{job_id}`

Poll for progress:

```json
{
  "job_id": "b3f1...",
  "status": "running",
  "phase": "gpx",
  "progress": 0.3,
  "indexed": 120,
  "total": 0,
  "errors": 0,
  "started_at": "2024-08-12T09:00:00Z",
  "finished_at": null
}
```

`status` is one of `running`, `done`, `error`. `phase` is one of `import`, `gpx`, `clustering`, `interpolation`, `elevation`, `thumbnails`, `done`. `404` if the job ID is unknown (job state is in-memory, lost on server restart).

### `POST /api/reindex`

Body: `{"confirm": true}` (required, `400` otherwise). Clears photos, quests, GPX files and the geocode cache, then returns `{"status": "cleared"}`. Does not touch original files.

## Search

### `GET /api/search/geocode?q=...`

Proxies Nominatim geocoding (`q` min length 2), caching results in `geocode_cache`. Cache hits skip the network call entirely.

```json
[{"display_name": "Chamonix, France", "lat": 45.9, "lon": 6.87, "bbox_lat_min": 45.8, "bbox_lat_max": 46.0, "bbox_lon_min": 6.7, "bbox_lon_max": 7.0}]
```

Bounding box fields are `null` on cache hits (not stored in the cache table).

## Tiles

### `GET /api/tiles/{layer}/{z}/{x}/{y}`

Proxies and caches map tiles for `layer` in `osm`, `topo`, `satellite` (see [ADR 0015](../adr/0015-osm-layer-alternatives-per-layer-cache.md)). Served from the filesystem cache if present, otherwise fetched from the upstream tile server and cached. `404` for an unknown layer, `502` if the upstream fetch fails.

### `GET /api/tiles/{z}/{x}/{y}.png`

Legacy route, redirects to `/api/tiles/osm/{z}/{x}/{y}`.

## Real-time events

### `GET /api/events`

Server-Sent Events stream (`text/event-stream`). Publishes `import_progress` events during the import pipeline (same fields as the job status polling response) and `import_error` on failure. Not currently consumed by the frontend, see [frontend architecture](../architecture/frontend_architecture.md).
