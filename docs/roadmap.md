[🇫🇷 Version française](roadmap.fr.md) | 🇬🇧 English version

---

# Roadmap - Stamped

## v1 - Delivered

- [x] **Phase 0** - Repository, tooling, CI
- [x] **Phase 1** - Backend skeleton (FastAPI, SQLite, SSE, config)
- [x] **Phase 2** - Import pipeline (EXIF, GPX, quest clustering, GPS interpolation, elevation, thumbnails)
- [x] **Phase 3** - Thumbnail generation (Pillow, EXIF orientation, priority queue)
- [x] **Phase 4** - Map & frontend (Leaflet, clustering, filters, lightbox, GPX polylines)
- [x] **Phase 5** - Storyline (per-quest photo list, quest renaming, GPX export)
- [x] **Phase 6** - Orphan management (manual placement, bulk placement, photo deletion, deleted-hash blocklist)
- [x] **Phase 7** - Desktop layout (CSS Grid, font scale, boilerplate cleanup)

## v2 - Delivered

- [x] Synchronized storyline <-> map - hover on a photo highlights the map marker, and vice versa
- [x] "Photos without quest" view - photos with `quest_id = NULL`, with placement and deletion actions
- [x] Global photo browser - all photos with orphan status filter
- [x] Alternative OSM layers (topo, satellite) - with filesystem tile cache per layer
- [x] Elevation profile - collapsible panel below the map, SVG chart with distance axis, synced with storyline hover

## v3 - Planned

- [ ] **Quest macro timeline** - full-width animated view replacing the content area; quests positioned by chronological midpoint (day precision); fixed-width blocks stacked vertically by density (oldest on top); collapsed "N quests" blocks when capacity exceeded; mouse-wheel zoom; click returns to normal view
- [ ] Wire the `stamped index <path>` CLI command to the import pipeline, or remove it if `POST /api/import` is deemed sufficient - currently a stub, see [docs/operations.md](operations.md)
- [ ] Folder watch - automatic import on file change
- [ ] RAW image support
- [ ] Export (JSON, filtered GPX)
- [ ] Activity type tagging
- [ ] Dark theme
- [ ] Keyboard shortcuts
