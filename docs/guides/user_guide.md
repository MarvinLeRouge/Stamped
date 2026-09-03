[🇫🇷 Version française](user_guide.fr.md) | 🇬🇧 English version

---

# User Guide - Stamped

## Overview

Stamped turns a folder of photos and GPX tracks into a personal map of everywhere you have been. Point it at a folder; it reads EXIF and GPX data, groups photos into outings ("quests"), and displays everything on an OpenStreetMap-based map. See [docs/product-context.md](../product-context.md) for the underlying concept.

## Starting the app

```bash
stamped start
```

Opens the app in your browser at `http://localhost:8421`. See [docs/operations.md](../operations.md) for installation and configuration.

## Importing photos

> The in-app import trigger described in earlier project iterations is not available yet - starting an import currently requires a manual HTTP request. See [docs/operations.md](../operations.md) for the exact command, and the [roadmap](../roadmap.md) for the planned CLI/UI wiring.

Once an import is started, the map fills in progressively: photo positions appear first (from EXIF GPS or GPX interpolation), thumbnails follow shortly after.

## The map

- Geotagged photos appear as markers, clustered together when zoomed out.
- Click a cluster to zoom in and expand it; click a single marker to open the photo.
- Switch map layers (OpenStreetMap, topographic, satellite) using the layer selector.
- GPX tracks for the visible quests are drawn as polylines.

## Quests

A quest is an outing: a set of photos and GPX tracks taken close together in time (by default, less than 6 hours apart - configurable, see [docs/operations.md](../operations.md)). The sidebar lists all quests; selecting one opens its **storyline**, a chronological scrollable list of its photos.

- **Rename a quest** from the storyline panel; leave the name blank to fall back to the automatic date-based name.
- **Export a quest's GPX track** from the storyline panel.
- **Elevation profile** - a collapsible panel below the map shows altitude along the quest's GPX track; hovering the storyline or the chart cursor highlights the matching point in both.

## Orphan photos

A photo without a usable GPS position (no EXIF GPS, not covered by GPX interpolation) is an "orphan". Orphans are listed separately and can be placed on the map:

- **Individually** - click-to-place a single orphan photo at a chosen point on the map.
- **In bulk** - place all orphans of a quest at once, at the chronological median position of that quest's known GPS points.

Photos with no quest at all (`quest_id` unset) appear in a dedicated "photos without quest" view.

## Deleting a photo

Deleting a photo removes it from the app (database record and thumbnail) but never touches the original file on disk. Deleted photos are remembered so they are not re-imported if you run the import again over the same folder.

## Browsing all photos

A global photo browser lists every imported photo, independent of quest grouping, with a filter for orphan status.

## Working offline

After the first import of a geographic area, Stamped works entirely offline: map tiles and elevation data are cached locally. See [docs/operations.md](../operations.md#network-calls) for exactly what is fetched and when.
