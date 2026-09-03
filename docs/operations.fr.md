🇫🇷 Version française | [🇬🇧 English version](operations.md)

---

# Opérations - Stamped

## Prérequis

Python 3.12+, Node.js 18+.

## Installation

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git && cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && npm run build && cd ..
```

## Démarrage

```bash
stamped start
```

Ouvre `http://localhost:8421` dans le navigateur automatiquement (`--no-browser` pour désactiver). Si `frontend/dist/` est absent, `stamped start` le construit d'abord via `npm run build`. Se lie uniquement à `127.0.0.1`, voir [SECURITY.md](../SECURITY.fr.md).

## Importer des photos et des traces GPX

> **État actuel :** la commande CLI `stamped index <path>` décrite dans des versions antérieures de ce projet est un stub (`backend/stamped/cli.py`) - elle affiche un message et ne fait rien. Le seul moyen fonctionnel de démarrer un import aujourd'hui est l'API HTTP, serveur en cours d'exécution. Le câblage de cette commande CLI (ou sa suppression) est suivi dans la [roadmap](roadmap.fr.md).

Serveur en cours d'exécution (`stamped start`) :

```bash
curl -X POST http://localhost:8421/api/import \
  -H "Content-Type: application/json" \
  -d '{"path": "/chemin/absolu/vers/photos"}'
```

Retourne un ID de job ; interroger `GET /api/import/{job_id}` pour la progression, ou écouter `GET /api/events` (SSE) pour un suivi en temps réel des phases. Voir [docs/api/api_endpoints.md](api/api_endpoints.fr.md) pour le détail des requêtes/réponses.

Pour tout effacer et réimporter : `POST /api/reindex`.

## Vérifier l'état du système

```bash
stamped status
```

Affiche le nombre de photos, la progression des thumbnails, le nombre d'orphelines, le nombre de quests et le nombre de fichiers GPX. Nécessite que le serveur soit en cours d'exécution.

## Configuration

Variables d'environnement (préfixe `STAMPED_`), lues depuis `.env` à la racine du dépôt ou l'environnement du process :

| Variable | Défaut | Signification |
|---|---|---|
| `STAMPED_PORT` | `8421` | Port HTTP |
| `STAMPED_DATA_DIR` | `data` | Répertoire racine pour la base SQLite, les thumbnails et le cache de tuiles |
| `STAMPED_QUEST_GAP_HOURS` | `6` | Écart temporel utilisé pour séparer les photos en quests distinctes, voir [ADR 0006](adr/0006-quest-detection-temporal-clustering.md) |
| `STAMPED_THUMB_SIZE` | `400` | Taille des thumbnails générées, en pixels |
| `STAMPED_CAMERA_UTC_OFFSET_HOURS` | `0` | Décalage de l'horloge de l'appareil photo par rapport à l'UTC, voir [ADR 0013](adr/0013-camera-utc-offset-reconciliation.md) |

Exemple de `.env` :

```bash
STAMPED_CAMERA_UTC_OFFSET_HOURS=2   # ex. CEST
```

## Répertoire de données

```
data/
├── stamped.db     # base SQLite
├── thumbs/         # thumbnails générées, gitignored
└── tiles/           # tuiles de carte en cache, par couche, gitignored
```

Supprimer `data/` réinitialise l'app à un état vierge ; les photos originales ne sont jamais touchées (elles ne sont que lues, voir [ADR 0002](adr/0002-images-never-stored-in-database.md)).

## Appels réseau

| Appel | Quand | Mis en cache |
|---|---|---|
| Tuiles OSM | Premier affichage d'une zone sur la carte | Localement, indéfiniment |
| OpenTopoData | À l'import seulement | En SQLite |
| Nominatim | Géocodage des quests | En SQLite |

Après le premier import d'une zone géographique, Stamped fonctionne entièrement hors-ligne. Voir [SECURITY.md](../SECURITY.fr.md) pour le détail complet réseau/surface d'attaque.

## Tests et lint

```bash
make test          # backend + frontend
make test-backend   # pytest
make test-frontend    # vitest
make lint            # ruff, mypy, eslint, prettier check, vue-tsc
make format            # ruff format, eslint --fix, prettier --write
```
