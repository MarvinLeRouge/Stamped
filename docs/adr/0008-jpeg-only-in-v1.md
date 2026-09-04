# ADR 0008: JPEG only in v1

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/decisions.md` ADR-008

## Context

Supporting RAW formats (CR2, ARW, NEF, etc.) alongside JPEG would add significant complexity to EXIF extraction and thumbnail generation for v1.

## Decision

Only JPEG files are processed in v1. RAW formats are deferred; files in imported folders that are not JPEG are silently skipped (logged, not treated as an error).

## Consequences

- Simplifies EXIF extraction (`exifread`/`piexif`) and thumbnail generation (Pillow) to a single, well-supported format.
- Matches the developer's primary use case.
- RAW files sitting alongside JPEGs in an imported folder do not cause import errors; they are simply not indexed.

## Alternatives considered

Supporting RAW from the start was considered and deferred to a later version - tracked as a "RAW image support" item in the [roadmap](../roadmap.md).
