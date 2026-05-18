# Stamped

> Your outdoor photos on a conquest map. Fully private, nothing leaves your machine.

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
[![CI](https://github.com/MarvinLeRouge/Stamped/actions/workflows/ci.yml/badge.svg)](https://github.com/MarvinLeRouge/Stamped/actions)
[![codecov backend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=backend&label=backend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
[![codecov frontend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=frontend&label=frontend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
![License](https://img.shields.io/github/license/MarvinLeRouge/Stamped?cacheSeconds=3600)

Stamped is a local web app that turns your photo library and GPX tracks into a personal territory map. Import a folder, and every geotagged photo appears as a marker on the map. Explore by date, location, or quest. Nothing is uploaded anywhere.

---

## Concept

Each photo is proof of presence on the territory. Stamped doesn't ask you to organize or tag anything — it reads your files, detects your quests automatically, and shows you the extent of your documented world at a glance.

---

## Features (v1)

- **Conquest map** — all your geotagged photos on an OSM map, clustered by zoom level
- **Quest detection** — outings auto-detected by temporal clustering, optionally renamed
- **GPX support** — import tracks, interpolate position for photos without GPS
- **Offline-first** — OSM tiles cached locally, elevation data fetched once at import
- **Private by design** — no account, no cloud, no social features

---

## Stack

Python (FastAPI) · Vue 3 · SQLite · Leaflet · OpenTopoData

---

## Getting started

```bash
# Install
pip install stamped

# Start (opens browser automatically)
stamped start

# Import a folder of photos
stamped index ~/Photos/2024/rando-belledonne
```

---

## Status

| Phase | Description | Status |
|---|---|---|
| 0 | Repository & project setup | ✅ |
| 1A | Core — database & config | ✅ |
| 1B | Core — FastAPI server skeleton | ✅ |
| 1C | Core — frontend skeleton | ✅ |
| 2A–2D | Import pipeline (EXIF, GPX, quests, GPS interpolation) | ✅ |
| 2E–2F | Import pipeline (elevation, API & progress) | ⏳ |
| 3 | Thumbnail generation | ⏳ |
| 4 | Map & frontend filters | ⏳ |
| 5 | Storyline & quest detail | ⏳ |
| 6 | Orphan management & robustness | ⏳ |

---

## Privacy

Stamped makes three optional outbound network calls:

- **OSM tiles** — fetched on first map view, cached locally forever after
- **OpenTopoData** — elevation data fetched at import time only, cached in local DB
- **Nominatim** — reverse geocoding for quest auto-naming, cached in local DB

After first import of a zone, Stamped works entirely offline.

---

*Solo project · Local-first · No tracking · No ads*
