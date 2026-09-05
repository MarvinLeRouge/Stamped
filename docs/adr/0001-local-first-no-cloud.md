# ADR 0001: Local-first, no cloud

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/work-in-progress/decisions.md` ADR-001

## Context

Stamped manages a personal photo collection. The product's core value proposition is treating that collection as a private geographic record, not a shareable album, which rules out any design built around a server-side account or sync.

## Decision

Nothing leaves the machine except three optional outbound HTTP calls: OSM tile fetching, the OpenTopoData elevation API, and Nominatim geocoding. All three are cached locally after the first call. There is no user account, no cloud backend, no data synchronization.

## Consequences

- No sync, no backup, no account system to build or maintain.
- Single-user only by design; multi-device access is out of scope.
- After the first import of a geographic area, the app works fully offline.
- See [SECURITY.md](../../SECURITY.md) for the resulting attack-surface implications (no auth layer, localhost-only binding).

## Alternatives considered

Not explicitly recorded beyond the constraint itself; a cloud-backed or self-hosted-server model was never pursued given the privacy requirement driving the whole product.
