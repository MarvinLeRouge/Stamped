🇫🇷 Version française | [🇬🇧 English version](roadmap.md)

---

# Roadmap - Stamped

## v1 - Livré

- [x] **Phase 0** - Dépôt, outillage, CI
- [x] **Phase 1** - Squelette backend (FastAPI, SQLite, SSE, config)
- [x] **Phase 2** - Pipeline d'import (EXIF, GPX, clustering des quests, interpolation GPS, élévation, thumbnails)
- [x] **Phase 3** - Génération des thumbnails (Pillow, orientation EXIF, file prioritaire)
- [x] **Phase 4** - Carte et frontend (Leaflet, clustering, filtres, lightbox, polylines GPX)
- [x] **Phase 5** - Storyline (liste de photos par quest, renommage, export GPX)
- [x] **Phase 6** - Gestion des orphelines (placement manuel, placement en masse, suppression, liste noire des hash)
- [x] **Phase 7** - Layout desktop (CSS Grid, échelle typographique, nettoyage du boilerplate)

## v2 - Livré

- [x] Synchronisation storyline <-> carte - survol d'une photo met en évidence le marqueur, et inversement
- [x] Vue "Photos sans quest" - orphelines avec `quest_id = NULL`, avec actions de placement et suppression
- [x] Explorateur global de photos - filtre statut orphelin
- [x] Couches OSM alternatives (topo, satellite) - avec tile-cache filesystem par couche
- [x] Profil d'élévation - barre escamotable sous la carte, graphique SVG avec axe distance, synchronisé avec le survol de la storyline

## v3 - Prévu

- [ ] **Timeline macro des quests** - vue pleine largeur animée remplaçant la zone content ; quests positionnées par point médian chronologique (précision jour) ; blocs à largeur fixe empilés verticalement par densité (la plus ancienne en haut) ; blocs condensés "N quests" si capacité dépassée ; zoom molette souris ; clic retour vue normale
- [ ] Câbler la commande CLI `stamped index <path>` au pipeline d'import, ou la retirer si `POST /api/import` est jugé suffisant - actuellement un stub, voir [docs/operations.md](operations.fr.md)
- [ ] Surveillance de dossier - import automatique à la détection de nouveaux fichiers
- [ ] Support des fichiers RAW
- [ ] Export (JSON, GPX filtré)
- [ ] Tagging par type d'activité
- [ ] Thème sombre
- [ ] Raccourcis clavier
