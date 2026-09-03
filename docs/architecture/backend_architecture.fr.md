🇫🇷 Version française | [🇬🇧 English version](backend_architecture.md)

---

# Architecture backend - Stamped

## Vue d'ensemble

Le backend est une application FastAPI (`backend/stamped/`) servant une API REST sur `127.0.0.1:8421`. Il n'y a pas de couche d'authentification ; l'app est conçue pour tourner sur une seule machine de confiance.

## Structure

```
backend/stamped/
├── api/           # Routers FastAPI - parsing des requêtes, modèles de réponse Pydantic, orchestration
│   ├── photos.py
│   ├── quests.py
│   ├── imports.py
│   ├── search.py
│   ├── status.py
│   ├── tiles.py
│   └── main.py    # app factory, enregistrement des routers, lifespan (init_db au démarrage)
├── services/      # Logique métier - Python pur, aucun import FastAPI, aucun concept HTTP
│   ├── import_service.py
│   ├── quest_service.py
│   ├── thumb_service.py
│   ├── gpx_service.py
│   └── elevation_service.py
├── workers/       # Fonctions CPU-bound, sans état - reçoivent des données, retournent des données, pas d'accès DB
│   ├── exif_worker.py
│   ├── gpx_worker.py
│   ├── thumb_worker.py
│   └── elevation_worker.py
├── core/          # Préoccupations transverses
│   ├── db.py      # connexion sqlite3, exécution des migrations
│   ├── config.py  # pydantic-settings, variables d'env STAMPED_*
│   ├── events.py  # bus d'événements SSE
│   └── fs.py      # source de vérité unique pour la construction des chemins data/
└── cli.py         # `stamped start` / `stamped index` / `stamped status`
```

## Stack technique

Python 3.12+, FastAPI, uvicorn, `sqlite3` (bibliothèque standard), Pydantic. EXIF via `exifread` et `piexif`, GPX via `gpxpy`, thumbnails via Pillow, géocodage via `geopy` (Nominatim), altitude via `httpx` vers OpenTopoData. Le SSE est servi avec `sse-starlette`. `sqlmodel` est listé dans `pyproject.toml` mais n'est actuellement utilisé nulle part dans le code.

## Accès aux données

Stamped dialogue directement avec SQLite via le module standard `sqlite3` (requêtes paramétrées, row factory `sqlite3.Row`) - il n'y a pas d'ORM. Les formes de réponse sont déclarées comme des classes Pydantic `BaseModel` à côté de chaque router (ex. `PhotoSummary` dans `api/photos.py`), découplées du résultat SQL brut. Les schémas de tables vivent entièrement dans `migrations/*.sql`.

## Migrations

Les changements de schéma sont des scripts SQL versionnés (`migrations/001_init.sql`, `migrations/002_deleted_photos.sql`, ...), appliqués une seule fois chacun dans l'ordre du nom de fichier par `core/db.py::init_db()` au démarrage du process, suivis dans une table `schema_migrations`. Voir [ADR 0009](../adr/0009-versioned-sql-migrations-no-alembic.md) pour la justification de ce choix plutôt qu'un outil de migration ORM.

## Pipeline d'import

`POST /api/import` déclenche `services/import_service.py`, qui s'exécute en phases, chacune écrivant ses résultats immédiatement plutôt qu'en fin de pipeline (voir [ADR 0016](../adr/0016-async-phased-import-pipeline.md)) :

> **Note :** la commande CLI `stamped index <path>` est actuellement un stub (`backend/stamped/cli.py`) et n'appelle pas le pipeline d'import - voir [docs/operations.md](../operations.fr.md). Le seul moyen fonctionnel de démarrer un import aujourd'hui est `POST /api/import`.

1. **Indexation EXIF** - `workers/exif_worker.py` extrait l'heure de capture, le GPS, la marque/modèle d'appareil pour chaque JPEG ; les résultats sont écrits immédiatement pour que la carte soit utilisable avant la fin des phases suivantes.
2. **Parsing GPX + clustering des quests** - `workers/gpx_worker.py` parse les trackpoints ; `services/quest_service.py` regroupe les photos en quests par écart temporel (voir [ADR 0006](../adr/0006-quest-detection-temporal-clustering.md)) et associe les fichiers GPX aux quests.
3. **Interpolation GPS + enrichissement altitude** - les photos sans GPS EXIF sont interpolées à partir des trackpoints GPX environnants (jamais entre deux fichiers GPX différents, voir [ADR 0014](../adr/0014-gps-interpolation-single-gpx-file-boundary.md)) ; l'altitude est récupérée via OpenTopoData (voir [ADR 0004](../adr/0004-elevation-via-opentopodata-no-local-dem.md)).
4. **Génération des thumbnails** - `workers/thumb_worker.py` s'exécute en dernier, en arrière-plan, priorité la plus basse.

L'horloge de l'appareil photo vs l'heure UTC des fichiers GPX est réconciliée via un décalage configurable, appliqué de façon cohérente à l'interpolation, à l'association GPX-quest et à l'endpoint du profil d'élévation - voir [ADR 0013](../adr/0013-camera-utc-offset-reconciliation.md).

Les étapes CPU-bound tournent dans un `concurrent.futures.ProcessPoolExecutor` ; la progression est poussée au frontend via Server-Sent Events (`core/events.py`, `GET /api/events`) plutôt que par polling - voir [ADR 0007](../adr/0007-sse-for-realtime-progress.md).

## Service des tuiles et thumbnails statiques

`api/tiles.py` fait proxy vers des serveurs de tuiles compatibles OSM (plusieurs couches : OSM, topo, satellite) avec un cache filesystem par couche sous `data/tiles/{layer}/` (voir [ADR 0015](../adr/0015-osm-layer-alternatives-per-layer-cache.md)). Les thumbnails sont servis depuis `data/thumbs/{hash[:2]}/{hash}.jpg` via `api/photos.py`, générés à la demande s'ils sont absents plutôt que stockés en base (voir [ADR 0002](../adr/0002-images-never-stored-in-database.md)).

## Liste complète des endpoints

Voir [docs/api/api_endpoints.md](../api/api_endpoints.fr.md).
