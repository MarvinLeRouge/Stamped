# ADR 0009: Versioned SQL migration scripts, no Alembic

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Jean Ceugniet
**Sources:** `docs/ai/decisions.md` ADR-009

## Context

The database schema needs a way to evolve over time without a manual, error-prone `ALTER TABLE` process, for a project using raw `sqlite3` rather than an ORM.

## Decision

Database migrations are managed via versioned SQL scripts (`migrations/001_init.sql`, `migrations/002_*.sql`, ...), applied once each in filename order by `core/db.py::init_db()` at process startup, tracked in a `schema_migrations` table. No Alembic or other ORM migration tool is used.

## Consequences

- Migrations are plain, readable, diffable SQL - no Python migration DSL to learn or maintain.
- No auto-generation of migration diffs from model changes (there are no ORM models to diff against, see [backend architecture](../architecture/backend_architecture.md#data-access)); schema changes require writing the SQL by hand.
- A migration file, once applied anywhere, must never be edited - schema changes always take the form of a new numbered file.

## Alternatives considered

**Alembic** - rejected: adds significant complexity (revision graph, autogenerate, downgrade paths) that is not justified for a solo, single-file SQLite database with no ORM layer to generate diffs from in the first place.
