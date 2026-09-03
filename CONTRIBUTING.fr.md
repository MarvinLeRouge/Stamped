🇫🇷 Version française | [🇬🇧 English version](CONTRIBUTING.md)

---

# Contribuer à Stamped

C'est avant tout un projet personnel, local-first. Les contributions externes (rapports de bugs, corrections, petites améliorations) sont bienvenues mais limitées en périmètre.

## Prérequis

- Python 3.12+
- Node.js 18+

## Installation locale

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git
cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..

# Hooks git (pre-commit + pre-push)
pre-commit install
pre-commit install --hook-type pre-push
```

Ou plus simplement `make install`, qui fait tout ça d'un coup.

## Lancer les tests

```bash
make test            # backend + frontend
make test-backend     # pytest backend/tests/ --cov=backend/stamped
make test-frontend    # vitest --coverage --run
```

## Workflow

1. Forker le dépôt et créer une branche à partir de `main`.
2. Faire la modification, avec des tests qui la couvrent (voir [Tests](README.fr.md#-tests) dans le README).
3. Commiter en suivant la convention ci-dessous.
4. Pousser et ouvrir une pull request vers `main`.
5. La CI doit passer avant la revue.

## Nommage des branches

| Type | Préfixe |
|---|---|
| Fonctionnalité | `feat/description-courte` |
| Correction | `fix/description-courte` |
| Maintenance | `chore/description-courte` |
| Documentation | `docs/description-courte` |
| Refactoring | `refactor/description-courte` |
| Tests | `test/description-courte` |

Minuscules, kebab-case, sans caractères spéciaux.

## Convention de commit

Suivre [Conventional Commits](https://www.conventionalcommits.org/), impératif, minuscules, sans point final, avec une section `Modified files:` obligatoire :

```
<type>(<scope optionnel>): <résumé court>

Modified files:
- chemin/vers/fichier-a.ext - ce qui a été modifié
- chemin/vers/fichier-b.ext - ce qui a été modifié
```

Types : `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`, `ci`.

## Style de code

```bash
make lint             # ruff check + ruff format --check + mypy (backend), eslint + type-check (frontend)
make format            # ruff check --fix + ruff format (backend)
```

- **Backend** : `ruff` pour le lint/format, `mypy` en mode strict, annotations de type complètes sur chaque fonction.
- **Frontend** : `ESLint` + `Prettier`, Composition API avec `<script setup>` uniquement, pas d'Options API.
- **Tests** : miroir de la structure source (`backend/tests/` reflète `backend/stamped/`), livrés dans le même commit que la fonctionnalité couverte, jamais après.

La CI rejettera toute pull request qui ne passe pas ces vérifications.

## Code de conduite

Ce projet suit un [Code de conduite](CODE_OF_CONDUCT.md). En participant, vous vous engagez à le respecter.

## Licence

En contribuant, vous acceptez que vos contributions soient distribuées sous la [licence MIT](LICENSE) du projet.
