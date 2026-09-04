# ADR 0011: Photo deletion - DB only, original files untouched

**Status:** Accepted
**Date:** 2026-05-20
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/reflexions.md` ("Suppression de photos"), commit `240dc14` (feat: photo deletion, deleted_photos blocklist and map placement mode)

## Context

Users need to remove unwanted photos from the app (e.g. the individual frames of a panorama, no longer needed once the panorama itself is imported), without violating the non-negotiable constraint that original source files are never modified or deleted (see [ADR 0001](0001-local-first-no-cloud.md), [ADR 0002](0002-images-never-stored-in-database.md)).

## Decision

`DELETE /api/photos/{id}`:
1. Removes the `photos` database record.
2. Deletes the generated thumbnail file (`data/thumbs/`), a recomputable artifact.
3. Inserts the photo's SHA-256 hash into a `deleted_photos` blocklist table.
4. Recomputes `photo_count` and the bounding box of the associated quest.
5. Never touches the original file.

## Consequences

- Deletion is fully reversible from the user's perspective (the original file is untouched) but not reversible within the app itself without re-importing.
- Without the blocklist, running `POST /api/import` again on the same folder would silently re-import the deleted photo. The SHA-256 hash is already computed at import time for deduplication, so checking it against `deleted_photos` adds no extra cost - it reuses the same code path.
- The blocklist grows unbounded over time; no pruning mechanism exists as of this decision.

## Alternatives considered

Not explicitly recorded as separate options; the DB-only-deletion-plus-blocklist design follows directly from the non-negotiable read-only-originals constraint, leaving no real alternative for how deletion could work.
