🇫🇷 Version française | [🇬🇧 English version](README.md)

---

# Stamped

> *Une application web locale qui transforme votre bibliothèque de photos et vos traces GPX en carte personnelle de conquête — entièrement privée, rien ne quitte votre machine.*

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3-4FC08D?logo=vuedotjs&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
[![CI](https://github.com/MarvinLeRouge/Stamped/actions/workflows/ci.yml/badge.svg)](https://github.com/MarvinLeRouge/Stamped/actions)
[![codecov backend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=backend&label=backend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
[![codecov frontend](https://img.shields.io/codecov/c/github/MarvinLeRouge/Stamped?flag=frontend&label=frontend&logo=codecov)](https://codecov.io/gh/MarvinLeRouge/Stamped)
![License](https://img.shields.io/github/license/MarvinLeRouge/Stamped?cacheSeconds=3600)

---

## 💡 Concept

Les applications photo classiques vous demandent de tagger, organiser, décrire. Stamped ne demande rien. Pointez-le sur un dossier : il lit vos données EXIF et vos traces GPX, détecte automatiquement vos sorties, place chaque photo sur une carte et vous montre d'un coup d'œil l'étendue de votre territoire documenté.

Chaque photo géolocalisée est une preuve de présence. Stamped traite votre collection comme un relevé géographique, pas comme un album.

---

## 📊 Chiffres clés

| Métrique | Valeur |
|---|---|
| Tests backend | **208 passants** |
| Tests frontend | **146 passants** |
| Endpoints API | **19** |
| Couverture backend | **99%** |
| Couverture frontend | **97%** |
| Étapes du pipeline d'import | **6** (EXIF · GPX · quests · interpolation GPS · élévation · thumbnails) |

---

## 📸 Captures d'écran

### Toutes les quests

[![Toutes les quests](docs/screenshots/quests-all.png)](docs/screenshots/quests-all.png)

### Vue quest — profil d'élévation réduit

[![Vue quest — profil d'élévation réduit](docs/screenshots/quest-without-altitude.png)](docs/screenshots/quest-without-altitude.png)

### Survol d'un marqueur photo

[![Survol d'un marqueur photo](docs/screenshots/quest-hover-marker.png)](docs/screenshots/quest-hover-marker.png)

### Survol d'un cluster — synchro élévation

[![Survol d'un cluster — synchro élévation](docs/screenshots/quest-hover-cluster.png)](docs/screenshots/quest-hover-cluster.png)

### Survol d'un cluster ouvert

[![Survol d'un cluster ouvert](docs/screenshots/quest-hover-opened-cluster.png)](docs/screenshots/quest-hover-opened-cluster.png)

### Couche OSM alternative

[![Couche OSM alternative](docs/screenshots/quest-osm-alternate.png)](docs/screenshots/quest-osm-alternate.png)

---

## ✨ Fonctionnalités

- **Carte de conquête** — toutes les photos géolocalisées sur une carte OSM, clusterisées par niveau de zoom ; filtrage par quest, plage de dates ou zone géographique
- **Détection des quests** — sorties auto-détectées par clustering temporel (seuil configurable) ; renommage manuel possible
- **Storyline** — liste chronologique par quest avec timestamps, thumbnails et actions directes
- **Support GPX** — import de traces, affichage par polylines séparées, interpolation de position pour les photos sans GPS, export GPX de la quest
- **Gestion des orphelines** — photos sans coordonnées placées individuellement sur la carte (clic-pour-placer) ou en masse via le point médian chronologique des points GPS de la quest
- **Suppression de photos** — supprime le record en base et le thumbnail généré ; le fichier original n'est jamais touché ; les hash supprimés sont mis en liste noire pour éviter la réindexation
- **Offline-first** — tuiles OSM mises en cache localement dès le premier chargement ; données d'élévation enrichies une seule fois à l'import ; fonctionnement entièrement hors-ligne ensuite
- **Privé par conception** — pas de compte, pas de synchronisation cloud, pas d'analytics

---

## 🏗️ Architecture

```
backend/
├── stamped/
│   ├── api/           # Routes FastAPI — fines, sans logique métier
│   ├── services/      # Logique métier (import, quests, thumbnails, élévation, GPX)
│   ├── workers/       # Tâches CPU (extraction EXIF, parsing GPX, génération thumbnails, API élévation)
│   └── core/          # db.py · config.py · events.py (SSE) · fs.py
├── tests/             # Miroir de la structure source
migrations/            # Scripts SQL versionnés (pas d'outil de migration ORM)

frontend/
└── src/
    ├── components/    # MapView · QuestList · QuestStoryline · PhotoLightbox · StatusDashboard
    └── stores/        # photos · quests · lightbox · placement · status
```

### Schéma de base de données (SQLite)

| Table | Rôle |
|---|---|
| `photos` | Toutes les photos importées — métadonnées EXIF, GPS, statut thumbnail, flag orphelin |
| `quests` | Sorties auto-détectées — nom, bbox, nombre de photos |
| `gpx_files` | Fichiers GPX importés liés aux quests |
| `gpx_trackpoints` | Tous les points de trace avec horodatages |
| `deleted_photos` | Liste noire SHA-256 — empêche la réindexation des photos supprimées |
| `geocode_cache` | Cache du géocodage inverse Nominatim |
| `system_state` | Métadonnées d'import (date du dernier index) |

---

## 🧠 Décisions de conception

### COUNT live vs. compteur persistant pour les statistiques orphelines

`GET /api/status` exécute `SELECT COUNT(*) FROM photos WHERE is_orphan = 1` à chaque appel plutôt que de lire une valeur mise en cache. L'index `idx_photos_orphan` rend cette opération O(nombre d'orphelines) — sub-milliseconde quelle que soit la taille d'une collection personnelle. Un compteur persistant nécessiterait des mises à jour cohérentes dans quatre endpoints distincts (`PATCH /photos/{id}`, `DELETE /photos/{id}`, `POST /quests/{id}/place`, pipeline d'import) ; chaque oubli produit une dérive silencieuse. Ce bug a été rencontré en pratique : le compteur est devenu obsolète dès l'ajout du placement manuel. Sur SQLite avec index, les agrégats live sont plus fiables que les caches applicatifs, sauf mesure contraire.

### Suppression de photos — base de données uniquement, fichiers originaux intacts

`DELETE /api/photos/{id}` supprime le record en base et le thumbnail généré, puis insère le hash SHA-256 du fichier dans `deleted_photos`. Le fichier original n'est jamais modifié ni supprimé. Le SHA-256 est déjà calculé à l'import pour la déduplication — la vérification contre `deleted_photos` n'ajoute aucun coût au pipeline. Sans cette liste noire, `stamped index` sur le même dossier réimporterait la photo supprimée à la prochaine exécution.

### Point médian chronologique pour le placement en masse des orphelines

`POST /api/quests/{id}/place` utilise le point médian chronologique (trackpoints + photos géolocalisées, triés par horodatage, élément central) plutôt que le centroïde géométrique. Sur un aller-retour linéaire, la moyenne arithmétique des coordonnées tomberait au milieu du trajet — ce que fait aussi le médian, mais ancré dans le temps réel passé plutôt que dans l'espace géométrique. Sur une boucle, la moyenne peut sortir du sentier. La position placée est un point de départ ; l'utilisateur peut la surcharger avec des coordonnées explicites ou affiner photo par photo.

---

## 📡 API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/status` | État du système — comptage photos, orphelines, dernier import |
| `GET` | `/api/quests` | Toutes les quests triées par date |
| `PATCH` | `/api/quests/{id}` | Renommer une quest |
| `GET` | `/api/quests/{id}/photos` | Liste chronologique des photos d'une quest |
| `GET` | `/api/quests/{id}/trackpoints` | Segments GPX groupés par fichier |
| `GET` | `/api/quests/{id}/gpx` | Téléchargement GPX de la quest (fusionné si plusieurs fichiers) |
| `POST` | `/api/quests/{id}/place` | Place toutes les orphelines d'une quest au point médian GPS |
| `GET` | `/api/photos` | Liste de photos avec filtres bbox / date / quest / orphan |
| `PATCH` | `/api/photos/{id}` | Définir les coordonnées GPS, effacer le flag orphelin |
| `DELETE` | `/api/photos/{id}` | Supprimer de la base + thumbnail, mettre le hash en liste noire |
| `GET` | `/api/photos/{id}/thumb` | Servir le thumbnail généré (202 si en attente) |
| `GET` | `/api/photos/{id}/original` | Servir le fichier original |
| `POST` | `/api/photos/{id}/thumb/priority` | Priorité dans la file de génération |
| `POST` | `/api/import` | Démarrer le pipeline d'import, retourne un job ID |
| `GET` | `/api/import/{job_id}` | Statut et progression du job d'import |
| `POST` | `/api/reindex` | Réinitialiser et réimporter depuis zéro |
| `GET` | `/api/search/geocode` | Proxy Nominatim (résultats mis en cache) |
| `GET` | `/api/tiles/{z}/{x}/{y}.png` | Proxy tuiles OSM (cache filesystem) |
| `GET` | `/api/events` | Flux SSE pour la progression de l'import |

---

## 🧪 Tests

### Backend — pytest

```bash
make test-backend
# ou
python -m pytest backend/tests/ -v --cov=backend/stamped
```

- Base SQLite isolée par test (`tmp_path`, pas d'état partagé)
- Pipeline d'import testé de bout en bout avec de vrais fichiers JPEG et GPX
- Cas limites : interpolation GPS aux frontières de fichiers, déduplications inter-activités, échec de l'API d'élévation, orientation EXIF des thumbnails

### Frontend — Vitest

```bash
make test-frontend
# ou
cd frontend && npm run test:unit -- --coverage
```

- Environnement JSDOM, Vue Test Utils
- Stores Pinia testés en isolation
- Tests composants : interactions carte, mode placement, lightbox, flux renommage/suppression/placement de la Storyline

### Tout lancer

```bash
make test
```

---

## ⚙️ CI

[`ci.yml`](.github/workflows/ci.yml) — déclenché sur push et pull request :

1. **Lint** — ruff, mypy (backend) · ESLint, Prettier, vue-tsc (frontend)
2. **Tests backend** — pytest avec couverture, envoyé à Codecov (flag `backend`)
3. **Tests frontend** — Vitest avec couverture, envoyé à Codecov (flag `frontend`)
4. **Hook pre-push** — vue-tsc s'exécute localement avant chaque push

---

## 🚀 Démarrage

**Prérequis** — Python 3.12+, Node.js 18+

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git && cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && npm run build && cd ..

# Démarrage (ouvre automatiquement le navigateur sur http://localhost:8421)
stamped start

# Importer un dossier de photos et fichiers GPX
stamped index ~/Photos/2024/rando
```

Optionnel — décalage UTC de l'appareil photo (pour la précision de l'interpolation GPS) :

```bash
# .env
STAMPED_CAMERA_UTC_OFFSET_HOURS=2   # ex. CEST
```

---

## 🔒 Confidentialité

Stamped effectue trois appels réseau optionnels :

| Appel | Quand | Mis en cache |
|---|---|---|
| Tuiles OSM | Premier affichage d'une zone | Localement, indéfiniment |
| OpenTopoData | À l'import uniquement | Dans SQLite |
| Nominatim | Géocodage des quests | Dans SQLite |

Après le premier import d'une zone géographique, Stamped fonctionne entièrement hors-ligne.

---

## 🗺️ Roadmap

### ✅ v1 — Livré

- [x] **Phase 0** — Dépôt, outillage, CI
- [x] **Phase 1** — Squelette backend (FastAPI, SQLite, SSE, config)
- [x] **Phase 2** — Pipeline d'import (EXIF, GPX, clustering des quests, interpolation GPS, élévation, thumbnails)
- [x] **Phase 3** — Génération des thumbnails (Pillow, orientation EXIF, file prioritaire)
- [x] **Phase 4** — Carte et frontend (Leaflet, clustering, filtres, lightbox, polylines GPX)
- [x] **Phase 5** — Storyline (liste de photos par quest, renommage, export GPX)
- [x] **Phase 6** — Gestion des orphelines (placement manuel, placement en masse, suppression, liste noire des hash)
- [x] **Phase 7** — Layout desktop (CSS Grid, échelle typographique, nettoyage du boilerplate)

### ✅ v2 — Livré

- [x] Synchronisation storyline ↔ carte — survol d'une photo met en évidence le marqueur, et inversement
- [x] Vue "Photos sans quest" — orphelines avec `quest_id = NULL`, avec actions de placement et suppression
- [x] Explorateur global de photos — filtres statut orphelin
- [x] Couches OSM alternatives (topo, satellite) — avec tile-cache filesystem par couche
- [x] Profil d'élévation — barre escamotable sous la carte, graphique SVG avec axe distance, synchronisé avec le survol de la Storyline

### 🔜 v3 — Prévu

- [ ] **Timeline macro des quests** — vue pleine largeur animée remplaçant la zone content ; quests positionnées par point médian chronologique (précision jour) ; blocs à largeur fixe empilés verticalement par densité (la plus ancienne en haut) ; blocs condensés "N quests" si capacité dépassée ; zoom molette souris ; clic retour vue normale
- [ ] Surveillance de dossier — import automatique à la détection de nouveaux fichiers
- [ ] Support des fichiers RAW
- [ ] Export (JSON, GPX filtré)
- [ ] Tagging par type d'activité
- [ ] Thème sombre
- [ ] Raccourcis clavier

---

## 🛠️ Stack technique

| Couche | Technologie |
|---|---|
| Backend | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square) ![Python](https://img.shields.io/badge/Python_3.12-3776AB?logo=python&logoColor=white&style=flat-square) |
| Base de données | ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white&style=flat-square) migrations SQL versionnées |
| Frontend | ![Vue.js](https://img.shields.io/badge/Vue.js_3-4FC08D?logo=vuedotjs&logoColor=white&style=flat-square) ![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white&style=flat-square) |
| Carte | ![Leaflet](https://img.shields.io/badge/Leaflet-199900?logo=leaflet&logoColor=white&style=flat-square) + Leaflet.markercluster |
| État | ![Pinia](https://img.shields.io/badge/Pinia-FFD859?logo=pinia&logoColor=black&style=flat-square) |
| EXIF | Pillow |
| Tests backend | ![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white&style=flat-square) — 208 tests, 99% couverture |
| Tests frontend | ![Vitest](https://img.shields.io/badge/Vitest-6E9F18?logo=vitest&logoColor=white&style=flat-square) + Vue Test Utils — 146 tests, 97% couverture |
| Linting | ruff · mypy · ESLint · Prettier · vue-tsc |
| CI | ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white&style=flat-square) ![Codecov](https://img.shields.io/badge/Codecov-F01F7A?logo=codecov&logoColor=white&style=flat-square) |

---

## 📋 Licence

Ce projet est distribué sous licence MIT — voir le fichier [LICENSE](LICENSE) pour les détails.

---

*Projet solo · Local-first · Pas de tracking · Pas de pub*
