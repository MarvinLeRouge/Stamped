[🇫🇷 Version française](CONTRIBUTING.fr.md) | 🇬🇧 English version

---

# Contributing to Stamped

This is primarily a personal, local-first project. External contributions (bug reports, fixes, small improvements) are welcome but limited in scope.

## Prerequisites

- Python 3.12+
- Node.js 18+

## Local setup

```bash
git clone https://github.com/MarvinLeRouge/Stamped.git
cd Stamped

# Backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Frontend
cd frontend && npm install && cd ..

# Git hooks (pre-commit + pre-push)
pre-commit install
pre-commit install --hook-type pre-push
```

Or simply `make install`, which does all of the above.

## Running tests

```bash
make test           # backend + frontend
make test-backend    # pytest backend/tests/ --cov=backend/stamped
make test-frontend    # vitest --coverage --run
```

## Workflow

1. Fork the repository and create a branch off `main`.
2. Make your change, with tests covering it (see [Testing](README.md#-testing) in the README).
3. Commit following the convention below.
4. Push and open a pull request against `main`.
5. CI must pass before review.

## Branch naming

| Type | Prefix |
|---|---|
| Feature | `feat/short-description` |
| Bug fix | `fix/short-description` |
| Chore | `chore/short-description` |
| Documentation | `docs/short-description` |
| Refactor | `refactor/short-description` |
| Tests | `test/short-description` |

Use lowercase kebab-case. No special characters.

## Commit convention

Follow [Conventional Commits](https://www.conventionalcommits.org/), imperative mood, lowercase summary, no trailing period, with a mandatory `Modified files:` section:

```
<type>(<optional scope>): <short summary>

Modified files:
- path/to/file-a.ext - what was changed
- path/to/file-b.ext - what was changed
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`, `ci`.

## Code style

```bash
make lint            # ruff check + ruff format --check + mypy (backend), eslint + type-check (frontend)
make format           # ruff check --fix + ruff format (backend)
```

- **Backend**: `ruff` for lint/format, `mypy` in strict mode, full type annotations on every function.
- **Frontend**: `ESLint` + `Prettier`, Composition API with `<script setup>` only, no Options API.
- **Tests**: mirror the source structure (`backend/tests/` mirrors `backend/stamped/`), ship in the same commit as the feature they cover, never after.

CI will reject any pull request that fails these checks.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold it.

## License

By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
