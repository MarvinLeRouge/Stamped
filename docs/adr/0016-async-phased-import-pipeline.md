# ADR 0016: Phased, results-written-immediately import pipeline

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** commits `a33eb4e` (feat(import): implement EXIF extraction worker and import service, Phase 2A), `4ce40d0` (feat(import): implement GPX parser worker and import service, Phase 2B), `bd09842` (feat(import): implement GPS interpolation from GPX trackpoints, Phase 2D), `02b1959` (feat(import): implement elevation enrichment via OpenTopoData, Phase 2E), `3a1d69f` (feat(import): generate thumbnails automatically at end of import pipeline)

## Context

Importing a folder of photos and GPX tracks involves several independent, increasingly expensive steps (EXIF extraction, GPX parsing, quest clustering, GPS interpolation, elevation enrichment, thumbnail generation). Waiting for all of them to finish before showing anything would make the map unusable for a long time on a large import.

## Decision

The import pipeline (`services/import_service.py`, triggered by `POST /api/import`, see [backend architecture](../architecture/backend_architecture.md#import-pipeline)) runs as an ordered sequence of phases, each writing its results to the database immediately rather than staging results in memory until the end:

1. EXIF indexing - photo positions and metadata are written as soon as extracted.
2. GPX parsing + quest clustering.
3. GPS interpolation + elevation enrichment.
4. Thumbnail generation - runs last, in the background, lowest priority.

Progress for each phase is published over SSE (see [ADR 0007](0007-sse-for-realtime-progress.md)).

## Consequences

- The map becomes usable (photo markers visible) before thumbnails - the most expensive step - have finished generating.
- A failure partway through leaves earlier phases' results committed rather than rolling back the whole import, which is acceptable for a re-runnable, idempotent-by-hash pipeline.
- Each phase runs synchronously within the background task, in a fixed order - there is no parallelism between phases (only within a phase, via `ProcessPoolExecutor` for CPU-bound work).

## Alternatives considered

**A single all-or-nothing transaction covering the whole import** - would have simplified failure handling, but delays any usable output until the entire import (including thumbnail generation, the slowest phase) completes - rejected in favor of incremental visibility.
