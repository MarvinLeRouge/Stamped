[🇫🇷 Version française](architecture.fr.md) | 🇬🇧 English version

---

# Architecture - Stamped

> Public technical reference. See [backend architecture](architecture/backend_architecture.md) and [frontend architecture](architecture/frontend_architecture.md) for implementation details.

## Overview

Stamped is a two-process local web application:

- **Backend** - FastAPI (Python) on `127.0.0.1:8421`. Handles file indexing, EXIF extraction, GPX parsing, quest detection, thumbnail generation, and serves the REST API.
- **Frontend** - Vue 3 + Vite SPA. Served by the backend in production, Vite dev server in development. Displays the Leaflet map, quest list, storyline, and import dashboard.

Both processes communicate over the REST API. Import and thumbnail progress is pushed by the backend over Server-Sent Events (not currently consumed by the frontend, see [frontend architecture](architecture/frontend_architecture.md)).

## Project structure

```
stamped/
├── backend/
│   ├── stamped/
│   │   ├── api/          # FastAPI routes
│   │   ├── workers/      # CPU-bound subprocesses
│   │   ├── services/     # business logic
│   │   └── core/         # db, config, events, fs
│   └── tests/
├── frontend/
│   └── src/
├── data/                 # runtime, gitignored
├── migrations/           # versioned SQL scripts
└── docs/
    ├── architecture/      # backend/frontend architecture
    ├── adr/               # architecture decision records
    ├── api/                # API reference
    └── guides/              # developer/user guides
```

## Further reading

- [Backend architecture](architecture/backend_architecture.md)
- [Frontend architecture](architecture/frontend_architecture.md)
- [API reference](api/api_endpoints.md)
- [Architecture decision records](adr/README.md)
- [Product context](product-context.md)
- [Operations](operations.md)
