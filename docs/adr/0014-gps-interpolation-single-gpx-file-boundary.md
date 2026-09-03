# ADR 0014: GPS interpolation never crosses a GPX file boundary

**Status:** Accepted
**Date:** 2026-05-19
**Deciders:** Jean Ceugniet
**Sources:** commit `f37fdd5` (fix(import): prevent GPS interpolation across different GPX files)

## Context

Photos without EXIF GPS are interpolated from the two surrounding GPX trackpoints by timestamp. When those two surrounding trackpoints came from two different GPX files (e.g. two separate, unrelated activities recorded on the same day with a gap between them), the photo was interpolated along a straight line between two points that do not represent any real path the user walked.

## Decision

The trackpoint lookup used for interpolation includes the source `gpx_file_id`. If the two trackpoints surrounding a photo's timestamp belong to different GPX files, interpolation is skipped and the photo is left as an orphan instead of being placed on a meaningless straight line between two unrelated activities.

## Consequences

- Some photos that were previously (incorrectly) geolocated become orphans instead, requiring manual placement (see [ADR 0012](0012-chronological-median-orphan-placement.md)) - a deliberate trade-off: an orphan is honest about missing data, a wrong position is not.
- Interpolation quality now depends on GPX files not having gaps in coverage where photos were taken; this is inherent to the data, not something the app can compensate for further.

## Alternatives considered

Not explicitly recorded; the bug's fix left no viable alternative to skipping interpolation across a file boundary, since inventing a plausible position across two unrelated tracks provides no real signal.
