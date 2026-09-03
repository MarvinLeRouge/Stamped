# ADR 0010: Live COUNT vs. cached counter for orphan stats

**Status:** Accepted
**Date:** 2026-05-20
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/reflexions.md` ("Comptage des photos orphelines"), commit `808863c` (fix(status,ui): live status counts and real-time refresh after photo delete)

## Context

`GET /api/status` exposes an `orphans` count consumed by the status dashboard. It was initially stored as a persistent counter in `system_state`, updated at import time. That counter drifted as soon as operations outside the import pipeline modified `is_orphan` (manual placement, photo deletion) without also updating the cached value - a real bug encountered in practice.

## Decision

`GET /api/status` runs `SELECT COUNT(*) FROM photos WHERE is_orphan = 1` live, on every call, instead of reading a cached value.

## Consequences

- The `idx_photos_orphan` index (created in the initial migration) makes the query O(orphan count), not O(total photos) - sub-millisecond at any realistic personal-collection size.
- No risk of the counter drifting from reality: there is a single source of truth (the `photos` table), not a copy that must be kept in sync across every endpoint that touches `is_orphan` (`PATCH /photos/{id}`, `DELETE /photos/{id}`, `POST /quests/{id}/place`, the import pipeline).
- This trades a theoretical read-cost saving for correctness; a cached counter would only be justified at a scale (thousands of requests/second, millions of rows) well outside this tool's personal, single-user scope.

## Alternatives considered

**Persistent counter in `system_state` or a dedicated column** - this was the original implementation. Rejected after the drift bug: every new endpoint that modifies `is_orphan` becomes a silent-failure vector if it forgets to update the counter.
