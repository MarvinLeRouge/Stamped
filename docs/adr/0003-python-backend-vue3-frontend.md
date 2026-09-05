# ADR 0003: Python backend, Vue 3 frontend

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/decisions.md` ADR-003

## Context

The app needs a backend capable of geospatial processing (EXIF extraction, GPX parsing, GPS interpolation) and a frontend capable of rendering an interactive map with real-time updates.

## Decision

FastAPI (Python) for the backend, Vue 3 + Vite for the frontend, coupled through a local REST API on port 8421. Two separate processes at runtime; in development, the Vite dev server proxies API calls to the backend.

## Consequences

- Python's mature geospatial/EXIF/GPX ecosystem (`exifread`, `piexif`, `gpxpy`, `geopy`) is used directly rather than reimplemented.
- Two processes to run in development (`stamped start` builds and serves the frontend in production, collapsing this to one process for end users).
- Frontend and backend evolve as independent codebases with their own test suites and lint configs.

## Alternatives considered

Not explicitly recorded; the choice reflects the developer's existing skills and prior familiarity with both ecosystems.
