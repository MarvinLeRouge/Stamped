🇫🇷 Version française | [🇬🇧 English version](backend_developer_guide.md)

---

# Guide développeur backend - Stamped

Voir [architecture backend](../architecture/backend_architecture.fr.md) pour la structure et le pipeline d'import. Ce guide couvre les conventions au quotidien pour travailler dans `backend/stamped/`.

## Technologies

- Framework : FastAPI, servi par uvicorn
- Langage : Python 3.12+
- Base de données : SQLite, accédée via le module standard `sqlite3` (pas d'ORM)
- Validation / formes de réponse : Pydantic `BaseModel`
- Configuration : `pydantic-settings`, variables d'environnement `STAMPED_*` (voir [docs/operations.md](../operations.fr.md))

## Responsabilités des couches

- `api/` - routers FastAPI uniquement. Parse la requête, appelle `services/`, façonne la réponse Pydantic. Pas de logique métier, pas d'accès filesystem direct au-delà de servir une réponse.
- `services/` - logique métier en Python pur. Aucun import FastAPI, aucun concept HTTP (pas de `HTTPException`, pas de `Request`). Testable en appelant les fonctions directement avec une `sqlite3.Connection`.
- `workers/` - fonctions CPU-bound, sans état (extraction EXIF, parsing GPX, génération de thumbnails, requêtes d'élévation). Reçoivent des données, retournent des données, aucun accès DB - ce qui permet de les exécuter dans un `ProcessPoolExecutor` sans problème de partage de connexion.
- `core/` - préoccupations transverses : `db.py` (connexion + migrations), `config.py` (configuration), `events.py` (bus SSE), `fs.py` (source de vérité unique pour les chemins `data/`).

Avant d'ajouter un endpoint, se demander à quelle couche appartient la logique : si elle touche la base ou implique une décision, elle va dans `services/`, pas dans la fonction du router.

## Accès aux données

Il n'y a ni ORM ni classes de table SQLModel, bien que `sqlmodel` soit listé dans `pyproject.toml` - il n'est pas utilisé. Interroger la base directement :

```python
rows = conn.execute("SELECT id, lat, lon FROM photos WHERE quest_id = ?", (quest_id,)).fetchall()
```

- Toujours utiliser des requêtes paramétrées (placeholders `?`), jamais de SQL formaté par concaténation de chaînes.
- `conn` est une `sqlite3.Connection` avec `row_factory = sqlite3.Row`, injectée via `Depends(get_db)` dans les routes.
- Déclarer une classe Pydantic `BaseModel` à côté du router pour la forme de réponse, et la construire explicitement à partir de la row - ne pas retourner des objets `sqlite3.Row` bruts depuis un endpoint.
- Les schémas de tables vivent entièrement dans `migrations/*.sql`, jamais en Python. Voir [ADR 0009](../adr/0009-versioned-sql-migrations-no-alembic.md).

## Ajouter une migration

Ajouter un nouveau fichier `migrations/00N_description.sql` (numéro séquentiel suivant). Il est appliqué une seule fois, dans l'ordre du nom de fichier, par `core/db.py::init_db()` au démarrage, et suivi dans la table `schema_migrations`. Ne jamais modifier un fichier de migration déjà appliqué - en ajouter un nouveau à la place.

## Workers et pipeline d'import

Les étapes CPU-bound (EXIF, parsing GPX, thumbnails, élévation) passent par un `concurrent.futures.ProcessPoolExecutor`. Les fonctions des workers dans `workers/` doivent rester sans effet de bord au-delà de leur valeur de retour - pas de connexion DB, pas d'état mutable partagé - car elles peuvent s'exécuter dans un processus séparé. Voir [architecture backend](../architecture/backend_architecture.fr.md#pipeline-dimport) pour la séquence des phases.

## Progression en temps réel

Les mises à jour de progression sont publiées sur `core/events.py::bus` et diffusées via `GET /api/events` (SSE), pas par polling. Pour une nouvelle opération longue nécessitant un suivi de progression, publier via le même bus plutôt que d'inventer un nouveau mécanisme - voir [ADR 0007](../adr/0007-sse-for-realtime-progress.md).

## Tests

```bash
make test-backend
# ou
python -m pytest backend/tests/ -v --cov=backend/stamped
```

- Chaque test dispose d'une DB SQLite isolée (fixture `tmp_path`), pas d'état partagé entre tests.
- Préférer tester les fonctions de `services/` directement avec une vraie connexion SQLite (temporaire) plutôt que de mocker la base.
- Faire correspondre la structure de `backend/tests/` à celle de `backend/stamped/`.

## Lint

```bash
make lint-backend   # ruff, mypy
make format          # ruff format
```

Les annotations de type sont obligatoires partout ; `mypy` tourne en CI et via pre-commit.
