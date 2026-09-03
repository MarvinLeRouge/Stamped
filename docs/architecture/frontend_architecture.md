[🇫🇷 Version française](frontend_architecture.fr.md) | 🇬🇧 English version

---

# Frontend Architecture - Stamped

## Overview

Vue 3 + Vite SPA (`frontend/src/`), built with the Composition API and `<script setup>` only. Served by the FastAPI backend in production (`stamped start` builds `frontend/dist/` automatically if missing); the Vite dev server proxies API calls to `127.0.0.1:8421` in development.

## Layout

```
frontend/src/
├── App.vue              # root layout - CSS grid, mounts the map and side panels
├── main.ts              # app bootstrap
├── api/
│   └── index.ts         # single Axios instance, base URL /api
├── stores/               # Pinia stores, one per domain concern
│   ├── photos.ts
│   ├── quests.ts
│   ├── status.ts
│   ├── layer.ts          # active OSM/topo/satellite tile layer
│   ├── lightbox.ts        # open/close state for the photo lightbox
│   ├── placement.ts       # click-to-place orphan photo mode
│   ├── highlight.ts        # storyline <-> map hover synchronisation
│   └── elevation.ts        # elevation profile data for the selected quest
└── components/
    ├── MapView.vue         # Leaflet map, markers, clustering, GPX polylines
    ├── QuestList.vue        # sidebar list of quests
    ├── QuestStoryline.vue    # per-quest scrollable photo list, rename/delete/place actions
    ├── ElevationPanel.vue     # collapsible SVG elevation chart below the map
    ├── AllPhotosPanel.vue      # global photo browser with orphan filter
    ├── UnquestedPanel.vue       # photos with quest_id = NULL
    ├── LayerSelector.vue         # floating OSM/topo/satellite switcher
    ├── PhotoLightbox.vue          # fullscreen photo viewer
    └── StatusDashboard.vue         # import progress, counts
```

There is no `composables/` directory: state lives directly in Pinia stores.

## State management

Each Pinia store (Composition API `defineStore` with `setup` syntax) owns one concern and exposes its own `fetch`/action functions calling `api/index.ts` directly - there is no separate per-resource API module layer. Components read store state via `storeToRefs` and call store actions; they do not call Axios directly. Data is fetched on mount and re-fetched explicitly after mutating actions (e.g. the status store is re-fetched after a photo delete) rather than kept live via a persistent connection.

## Map <-> storyline synchronisation

`stores/highlight.ts` is the shared source of truth for "what's currently hovered": hovering a photo in `QuestStoryline` highlights its marker (or cluster) in `MapView`, and vice versa; `ElevationPanel` also listens to it to move the chart cursor to the matching point on the elevation profile.

## Build

`npm run build` runs `vue-tsc --build` (type-check) and `vite build` in parallel (`run-p`), emitting `frontend/dist/`, which the backend serves as static files in production. `npm run dev` starts the Vite dev server with hot module reload.

> The backend exposes an SSE endpoint (`GET /api/events`, see [backend architecture](backend_architecture.md)) for import/thumbnail progress, but the frontend does not currently open a connection to it - there is no in-app way to trigger or watch an import (see the open question flagged in [docs/operations.md](../operations.md) about the `stamped index` CLI command).
