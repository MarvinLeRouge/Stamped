# ADR 0002: Images never stored in the database

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/decisions.md` ADR-002

## Context

Original photos must remain untouched and safe (non-negotiable product constraint). Thumbnails need to be served quickly for the map and storyline views.

## Decision

Original photo files are never modified, moved, or stored in the database - they are only read for EXIF extraction. Generated thumbnails live in a filesystem mirror (`data/thumbs/{hash[:2]}/{hash}.jpg`). SQLite stores only file paths and metadata, never binary image data.

## Consequences

- Keeps the SQLite database small regardless of collection size.
- Originals are never at risk from a database bug or migration.
- The filesystem thumbnail cache and the database can diverge if the process crashes mid-write; thumbnails are treated as a recomputable artifact, not a source of truth (see [ADR 0011](0011-photo-deletion-db-only.md) for the same principle applied to deletion).

## Alternatives considered

Storing thumbnails as BLOBs in SQLite was not pursued - it would grow the database file substantially and complicate backup/restore of a file that is meant to stay small.
