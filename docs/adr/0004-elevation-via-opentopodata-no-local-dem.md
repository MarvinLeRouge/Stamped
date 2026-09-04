# ADR 0004: Elevation via OpenTopoData, no local DEM

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/decisions.md` ADR-004

## Context

Quest elevation profiles need altitude data for GPX trackpoints. The initial architecture considered local SRTM digital elevation model (DEM) files, read via the `elevation` package and `rasterio`/GDAL.

## Decision

Elevation enrichment goes exclusively through the OpenTopoData API (Mapzen model), called once per import and cached permanently in the database. No `rasterio`, no GDAL, no local DEM files are used.

## Consequences

- Internet connectivity is required when importing new photos/GPX (see [ADR 0001](0001-local-first-no-cloud.md)); once cached, elevation data is available offline.
- If OpenTopoData is unreachable at import time, elevation is left unset and can be backfilled by re-running the import.
- Avoids a heavy GDAL dependency and tens of megabytes of DEM tile downloads per degree of coverage.

## Alternatives considered

**Local SRTM tiles via `rasterio`/GDAL** - rejected: SRTM downloads are 25-80 MB per 1x1 degree tile, and GDAL is a heavy dependency for a solo local-first tool. OpenTopoData was already familiar to the developer from another project.
