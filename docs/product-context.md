[🇫🇷 Version française](product-context.fr.md) | 🇬🇧 English version

---

# Product Context - Stamped

## Concept

Standard photo apps ask you to tag, organize and describe. Stamped doesn't. Point it at a folder, and it reads your EXIF data and GPX tracks, detects your outings automatically, places every photo on a map, and shows you the extent of your documented territory at a glance.

Each geotagged photo is evidence of presence. Stamped treats your collection as a geographic record, not an album.

## Target user

A single user managing their own personal photo collection on their own machine. No multi-user support, no accounts, no sharing features. See [ADR 0001](adr/0001-local-first-no-cloud.md) for the local-first rationale.

## Core vocabulary

| Term | Meaning |
|---|---|
| `quest` | An outing - a set of photos and GPX tracks grouped by temporal proximity (see [ADR 0005](adr/0005-quest-as-canonical-term.md), [ADR 0006](adr/0006-quest-detection-temporal-clustering.md)) |
| `orphan` | A photo with no geographic position (no EXIF GPS, not covered by GPX interpolation) |
| `thumb` | A generated thumbnail, stored on the filesystem, never in the database |

## Features

- **Conquest map** - all geotagged photos on an OSM map, clustered by zoom level; filter by quest, date range or bounding box
- **Quest detection** - outings auto-detected by temporal clustering (configurable gap); quests renameable
- **Storyline** - per-quest scrollable photo list with timestamps, thumbnails and inline actions
- **GPX support** - import tracks, display per-file polylines, interpolate position for photos without GPS coordinates, export quest GPX
- **Orphan management** - photos without coordinates placed individually on the map (click-to-place) or in bulk via chronological median of quest GPS points
- **Photo deletion** - removes DB record and generated thumbnail; original file is never touched; deleted hashes blocklisted to prevent re-indexing
- **Offline-first** - OSM tiles cached locally after first fetch; elevation data enriched once at import; full offline operation after initial run
- **Private by design** - no account, no cloud sync, no analytics

## Non-goals

- Multi-user accounts or sharing
- Cloud storage or sync
- Photo editing
- Social features (comments, likes, public feeds)
