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

Application en deux processus : backend FastAPI sur `127.0.0.1:8421`, frontend Vue 3 + Vite. Voir [docs/architecture.fr.md](docs/architecture.fr.md) pour la vue d'ensemble, [docs/architecture/backend_architecture.fr.md](docs/architecture/backend_architecture.fr.md) et [docs/architecture/frontend_architecture.fr.md](docs/architecture/frontend_architecture.fr.md) pour les détails d'implémentation, et [docs/adr/](docs/adr/README.md) pour les décisions de conception (compteur live vs cache, liste noire de suppression, placement médian, décrites auparavant ici). Note : les ADR sont rédigées en anglais uniquement.

---

## 📡 API

Référence complète des requêtes/réponses : [docs/api/api_endpoints.fr.md](docs/api/api_endpoints.fr.md), une référence statique et versionnée, la documentation Swagger en direct sur `/docs` n'étant accessible qu'une fois l'application installée et démarrée.

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
curl -X POST http://localhost:8421/api/import -H "Content-Type: application/json" -d '{"path": "/home/vous/Photos/2024/rando"}'
```

Note : la commande CLI `stamped index <path>` décrite dans d'anciennes versions de ce README est actuellement un stub et ne déclenche aucun import. L'appel `POST /api/import` ci-dessus est aujourd'hui le seul moyen fonctionnel d'en démarrer un, voir [docs/operations.fr.md](docs/operations.fr.md) pour les détails et [docs/roadmap.fr.md](docs/roadmap.fr.md) pour le plan de raccordement de la commande CLI.

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

v1 et v2 sont livrées ; la v3 (timeline macro des quests, surveillance de dossier, support RAW, exports, tagging par activité, thème sombre, raccourcis clavier) est prévue. Détail complet : [docs/roadmap.fr.md](docs/roadmap.fr.md).

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
