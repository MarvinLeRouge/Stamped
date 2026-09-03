🇫🇷 Version française | [🇬🇧 English version](frontend_architecture.md)

---

# Architecture frontend - Stamped

## Vue d'ensemble

SPA Vue 3 + Vite (`frontend/src/`), construite avec la Composition API et `<script setup>` uniquement. Servie par le backend FastAPI en production (`stamped start` construit `frontend/dist/` automatiquement si absent) ; le serveur de dev Vite fait proxy des appels API vers `127.0.0.1:8421` en développement.

## Structure

```
frontend/src/
├── App.vue              # layout racine - grille CSS, monte la carte et les panneaux latéraux
├── main.ts               # bootstrap de l'app
├── api/
│   └── index.ts          # instance Axios unique, base URL /api
├── stores/                # stores Pinia, un par domaine
│   ├── photos.ts
│   ├── quests.ts
│   ├── status.ts
│   ├── layer.ts           # couche de tuiles active OSM/topo/satellite
│   ├── lightbox.ts         # état ouvert/fermé de la lightbox photo
│   ├── placement.ts         # mode clic-pour-placer une photo orpheline
│   ├── highlight.ts          # synchro survol storyline <-> carte
│   └── elevation.ts           # données du profil d'élévation pour la quest sélectionnée
└── components/
    ├── MapView.vue          # carte Leaflet, marqueurs, clustering, polylines GPX
    ├── QuestList.vue         # liste des quests dans la sidebar
    ├── QuestStoryline.vue     # liste chronologique par quest, actions renommer/supprimer/placer
    ├── ElevationPanel.vue      # graphique SVG d'élévation escamotable sous la carte
    ├── AllPhotosPanel.vue       # explorateur global de photos avec filtre orphelin
    ├── UnquestedPanel.vue        # photos avec quest_id = NULL
    ├── LayerSelector.vue          # sélecteur flottant OSM/topo/satellite
    ├── PhotoLightbox.vue           # visionneuse photo plein écran
    └── StatusDashboard.vue          # progression de l'import, compteurs
```

Il n'y a pas de dossier `composables/` : l'état vit directement dans les stores Pinia.

## Stack technique

Vue 3, Vite, TypeScript, Pinia, Axios. Rendu de la carte via Leaflet, `@vue-leaflet/vue-leaflet` et `leaflet.markercluster`. Tests avec Vitest et `@vue/test-utils`. Lint avec ESLint, formatage avec Prettier.

## Gestion d'état

Chaque store Pinia (Composition API, syntaxe `setup` de `defineStore`) gère un seul domaine et expose ses propres fonctions `fetch`/actions appelant directement `api/index.ts` - il n'y a pas de couche de modules API séparée par ressource. Les composants lisent l'état des stores via `storeToRefs` et appellent les actions des stores ; ils n'appellent jamais Axios directement. Les données sont récupérées au montage et re-récupérées explicitement après une action de mutation (ex. le store status est re-fetché après suppression d'une photo) plutôt que maintenues à jour via une connexion persistante.

## Synchronisation carte <-> storyline

`stores/highlight.ts` est la source de vérité partagée pour "ce qui est survolé actuellement" : survoler une photo dans `QuestStoryline` met en évidence son marqueur (ou son cluster) dans `MapView`, et inversement ; `ElevationPanel` écoute aussi ce store pour déplacer le curseur du graphique au point correspondant du profil d'élévation.

## Build

`npm run build` lance `vue-tsc --build` (vérification de types) et `vite build` en parallèle (`run-p`), produisant `frontend/dist/`, servi par le backend en tant que fichiers statiques en production. `npm run dev` démarre le serveur de dev Vite avec hot module reload.

> Le backend expose un endpoint SSE (`GET /api/events`, voir [architecture backend](backend_architecture.fr.md)) pour la progression de l'import/des thumbnails, mais le frontend n'ouvre actuellement aucune connexion dessus - il n'y a pas d'UI pour déclencher ou suivre un import (voir la remarque dans [docs/operations.md](../operations.fr.md) sur la commande CLI `stamped index`).
