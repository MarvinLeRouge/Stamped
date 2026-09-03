# Architecture Decision Records - Stamped

Index of accepted architecture decisions. See each ADR for full context, consequences and alternatives considered. Unlike the rest of this repository's documentation, ADRs are English-only.

| ADR | Title | Date |
|---|---|---|
| [0001](0001-local-first-no-cloud.md) | Local-first, no cloud | 2026-05-15 |
| [0002](0002-images-never-stored-in-database.md) | Images never stored in the database | 2026-05-15 |
| [0003](0003-python-backend-vue3-frontend.md) | Python backend, Vue 3 frontend | 2026-05-15 |
| [0004](0004-elevation-via-opentopodata-no-local-dem.md) | Elevation via OpenTopoData, no local DEM | 2026-05-15 |
| [0005](0005-quest-as-canonical-term.md) | "quest" as the canonical term for an outdoor activity | 2026-05-15 |
| [0006](0006-quest-detection-temporal-clustering.md) | Quest detection by temporal clustering (6h gap) | 2026-05-15 |
| [0007](0007-sse-for-realtime-progress.md) | SSE for real-time progress, not WebSockets | 2026-05-15 |
| [0008](0008-jpeg-only-in-v1.md) | JPEG only in v1 | 2026-05-15 |
| [0009](0009-versioned-sql-migrations-no-alembic.md) | Versioned SQL migration scripts, no Alembic | 2026-05-15 |
| [0010](0010-live-count-vs-cached-orphan-counter.md) | Live COUNT vs. cached counter for orphan stats | 2026-05-20 |
| [0011](0011-photo-deletion-db-only.md) | Photo deletion - DB only, original files untouched | 2026-05-20 |
| [0012](0012-chronological-median-orphan-placement.md) | Chronological median for bulk orphan placement | 2026-05-19 |
| [0013](0013-camera-utc-offset-reconciliation.md) | Camera UTC offset reconciliation | 2026-05-17 |
| [0014](0014-gps-interpolation-single-gpx-file-boundary.md) | GPS interpolation never crosses a GPX file boundary | 2026-05-19 |
| [0015](0015-osm-layer-alternatives-per-layer-cache.md) | OSM layer alternatives with per-layer tile cache | 2026-05-21 |
| [0016](0016-async-phased-import-pipeline.md) | Phased, results-written-immediately import pipeline | 2026-05-15 |
