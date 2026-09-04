# ADR 0005: "quest" as the canonical term for an outdoor activity

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/decisions.md` ADR-005

## Context

The app needed a single term for "an outdoor outing" (a set of photos and GPX tracks from one activity), used consistently across the database schema, API, frontend components, CLI output, and user-facing labels. Candidates considered: "outing", "hike", "run", "roam", "quest".

## Decision

`quest` is the canonical term, used everywhere: the `quests` table, the `quest_id` foreign key, `/api/quests` endpoints, the `QuestList`/`QuestStoryline` Vue components, CLI output, and user-facing labels.

## Consequences

- Naming is consistent end to end: no translation layer between an internal name and a user-facing label.
- The term is documented in [docs/product-context.md](../product-context.md) as core vocabulary for anyone new to the codebase.

## Alternatives considered

- **"outing"** - rejected as obscure/uncommon in casual use.
- **"hike"** - rejected as too specific, implies walking only (the app also covers cycling, trail running, etc.).
- **"run"** - rejected due to collision with process-execution terminology in code and logs.
- **"roam"** - considered but dropped in favor of "quest", which is semantically neutral and coherent with the "conquest map" product concept.
