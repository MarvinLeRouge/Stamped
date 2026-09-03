[🇫🇷 Version française](backend_developer_guide.fr.md) | 🇬🇧 English version

---

# Backend Developer Guide - Stamped

See [backend architecture](../architecture/backend_architecture.md) for the layout and import pipeline overview. This guide covers day-to-day conventions for working in `backend/stamped/`.

## Technologies

- Framework: FastAPI, served by uvicorn
- Language: Python 3.12+
- Database: SQLite, accessed via the standard library `sqlite3` module (no ORM)
- Validation / response shapes: Pydantic `BaseModel`
- Settings: `pydantic-settings`, `STAMPED_*` environment variables (see [docs/operations.md](../operations.md))

## Layer responsibilities

- `api/` - FastAPI routers only. Parse the request, call into `services/`, shape the Pydantic response. No business logic, no direct file-system access beyond serving a response.
- `services/` - business logic in pure Python. No FastAPI imports, no HTTP concepts (no `HTTPException`, no `Request`). Testable by calling functions directly with a `sqlite3.Connection`.
- `workers/` - CPU-bound, stateless functions (EXIF extraction, GPX parsing, thumbnail generation, elevation lookups). Receive data, return data, no DB access - keeps them runnable in a `ProcessPoolExecutor` without connection-sharing issues.
- `core/` - cross-cutting concerns: `db.py` (connection + migrations), `config.py` (settings), `events.py` (SSE bus), `fs.py` (single source of truth for `data/` paths).

When adding a new endpoint, ask which layer the logic belongs to before writing it: if it touches the database or has a decision to make, it belongs in `services/`, not in the router function.

## Database access

There is no ORM and no SQLModel table classes despite `sqlmodel` being listed in `pyproject.toml` - it is unused. Query the database directly:

```python
rows = conn.execute("SELECT id, lat, lon FROM photos WHERE quest_id = ?", (quest_id,)).fetchall()
```

- Always use parameterized queries (`?` placeholders), never string-formatted SQL.
- `conn` is a `sqlite3.Connection` with `row_factory = sqlite3.Row`, injected via `Depends(get_db)` in routes.
- Declare a Pydantic `BaseModel` next to the router for the response shape, and build it explicitly from the row - don't return raw `sqlite3.Row` objects from an endpoint.
- Table schemas live entirely in `migrations/*.sql`, never in Python. See [ADR 0009](../adr/0009-versioned-sql-migrations-no-alembic.md).

## Adding a migration

Add a new `migrations/00N_description.sql` file (next sequential number). It is applied once, in filename order, by `core/db.py::init_db()` at startup, and tracked in the `schema_migrations` table. Never edit an already-applied migration file - add a new one instead.

## Workers and the import pipeline

CPU-bound steps (EXIF, GPX parsing, thumbnails, elevation) run through a `concurrent.futures.ProcessPoolExecutor`. Worker functions in `workers/` must stay side-effect free beyond their return value - no DB connections, no shared mutable state - since they may run in a separate process. See [backend architecture](../architecture/backend_architecture.md#import-pipeline) for the phase sequence.

## Real-time progress

Progress updates are published on `core/events.py::bus` and streamed over `GET /api/events` (SSE), not polled. If a new long-running operation needs progress reporting, publish through the same bus rather than inventing a new mechanism - see [ADR 0007](../adr/0007-sse-for-realtime-progress.md).

## Testing

```bash
make test-backend
# or
python -m pytest backend/tests/ -v --cov=backend/stamped
```

- Each test gets an isolated SQLite DB (`tmp_path` fixture), no shared state between tests.
- Prefer testing `services/` functions directly with a real (temp) SQLite connection over mocking the database.
- Mirror `backend/tests/` structure to `backend/stamped/`.

## Linting

```bash
make lint-backend   # ruff, mypy
make format          # ruff format
```

Type annotations are required everywhere; `mypy` runs in CI and via pre-commit.
