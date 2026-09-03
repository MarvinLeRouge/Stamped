# ADR 0006: Quest detection by temporal clustering (6h gap)

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/decisions.md` ADR-006

## Context

Photos need to be grouped into quests automatically, without manual tagging, based on when they were taken.

## Decision

Photos are grouped into quests by detecting gaps greater than a configurable threshold (default 6 hours, `STAMPED_QUEST_GAP_HOURS`) between consecutive photos sorted by `captured_at`. Everything between two gaps forms one quest.

## Consequences

- Simple, deterministic, no machine learning or manual tagging required.
- Covers realistic single-day-or-shorter outdoor activity durations out of the box.
- Multi-day expeditions with overnight gaps are split into separate quests - accepted as a known limitation for v1, not addressed by this ADR.
- The threshold is a single global setting, not per-quest or per-activity-type configurable.

## Alternatives considered

Not explicitly recorded beyond the chosen approach; clustering by geographic proximity or activity-type heuristics was not pursued in favor of the simpler, deterministic temporal-gap method.
