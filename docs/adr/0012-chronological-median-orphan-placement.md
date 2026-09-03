# ADR 0012: Chronological median for bulk orphan placement

**Status:** Accepted
**Date:** 2026-05-19
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/reflexions.md` ("Placement des photos orphelines"), commits `aa7d6c2` (feat(api): add POST /api/quests/{id}/place for mass orphan placement), `4824793` (fix(api): recompute quest bbox after orphan placement)

## Context

`POST /api/quests/{id}/place` assigns a single reference position to all orphan photos of a quest at once, when no explicit coordinates are given. A reference point had to be chosen from the quest's known GPS points (GPX trackpoints and already-geolocated photos).

## Decision

Use the chronological median GPS point: all known points sorted by timestamp, the middle element by position in that sequence - not the geometric centroid (arithmetic mean of latitude/longitude).

## Consequences

- On a linear out-and-back route, the median and the geometric mean both fall roughly mid-trail, but the median stays anchored to where the user actually spent time, not to abstract geometric space.
- On a loop route, the geometric mean can fall off the trail entirely (e.g. in the middle of the enclosed area); the chronological median cannot, since it is always one of the real recorded points.
- The placed position is only a starting point - the same endpoint accepts explicit `lat`/`lon` to override it, and photos can be refined individually afterward via `PATCH /api/photos/{id}`.

## Alternatives considered

**Geometric centroid (arithmetic mean of all GPS points)** - simpler to compute, but rejected because it can place the reference point somewhere the user never actually was, particularly on loop routes.
