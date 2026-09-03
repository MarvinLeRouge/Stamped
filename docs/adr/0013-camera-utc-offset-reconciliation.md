# ADR 0013: Camera UTC offset reconciliation

**Status:** Accepted
**Date:** 2026-05-17
**Deciders:** Jean Ceugniet
**Sources:** PR #14 (`feat/exif-utc-offset`), commits `d9c6b95` (feat(import): add camera UTC offset support for GPS interpolation), `2bdccdd` (fix(quests): apply camera UTC offset when matching GPX files to quests), `b9a7632` (fix(elevation): shift trackpoint timestamps by camera UTC offset for correct photo sync)

## Context

Camera clocks store capture time as local time with no timezone information, while GPX trackpoints are recorded in UTC. Without reconciling the two, GPS interpolation and GPX-to-quest matching compare timestamps from different reference frames, producing wrong results whenever the camera's local time differs from UTC (e.g. any timezone other than UTC+0, or a misconfigured camera clock) - this surfaced as a real bug ("TheFranceFlag" scenario referenced in the source commits) where GPX association silently failed.

## Decision

Introduce a single configurable setting, `STAMPED_CAMERA_UTC_OFFSET_HOURS` (default `0`), applied consistently everywhere camera-local and GPX-UTC timestamps are compared:

- GPS interpolation from GPX trackpoints (`services/import_service.py`).
- Matching GPX files to quests by time range (`services/quest_service.py`).
- The elevation profile endpoint, which shifts trackpoint timestamps so they align with photo `captured_at` values (`api/quests.py`).

## Consequences

- A single setting must be kept correct by the user for their camera/timezone; there is no automatic detection of the camera's actual offset.
- All three consumers (interpolation, quest matching, elevation) must apply the offset the same way - a future change to one must be checked against the other two to avoid re-introducing the original bug.
- See [docs/operations.md](../operations.md) for how to configure this setting.

## Alternatives considered

Not explicitly recorded; per-photo or per-camera-model offset detection was not pursued in favor of a single global setting, consistent with the tool's single-user, single-collection scope.
