# ADR 0015: OSM layer alternatives with per-layer tile cache

**Status:** Accepted
**Date:** 2026-05-21
**Deciders:** Jean Ceugniet
**Sources:** commit `31fd5a2` (feat(map): add OSM layer alternatives with per-layer tile cache, V2-04)

## Context

Standard OSM street tiles are not always the most useful basemap for reviewing outdoor activities - topographic detail or satellite imagery is often more relevant for hiking or off-trail quests. The existing tile proxy (single OSM layer, single filesystem cache) needed to support multiple tile sources.

## Decision

`GET /api/tiles/{layer}/{z}/{x}/{y}` supports three named layers - `osm`, `topo` (OpenTopoMap), `satellite` (ArcGIS World Imagery) - each proxied from its own upstream and cached separately on the filesystem under `data/tiles/{layer}/`. The legacy `GET /api/tiles/{z}/{x}/{y}.png` route is kept as a redirect to the `osm` layer for backward compatibility. The frontend gained a `stores/layer.ts` store and a `LayerSelector.vue` component to switch between them.

## Consequences

- Disk usage under `data/tiles/` scales with the number of layers actually used, since each layer caches independently.
- Adding a further layer means adding an entry to the `_LAYERS` dict in `api/tiles.py` plus a cache subdirectory - no schema or API contract change needed.
- The legacy single-layer route stays functional for anything still calling it directly, redirecting rather than breaking.

## Alternatives considered

Not explicitly recorded; a single shared cache keyed only by `{z}/{x}/{y}` (ignoring layer) was the implicit prior state and was replaced rather than evaluated, since it cannot represent multiple tile sources for the same coordinates.
