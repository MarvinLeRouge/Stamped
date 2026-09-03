[🇫🇷 Version française](SECURITY.fr.md) | 🇬🇧 English version

---

# Security Policy

## Supported Versions

This project follows a single rolling `main` branch. There are no maintained release branches; only the latest commit on `main` is supported.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use GitHub's private vulnerability reporting: go to the [Security tab](https://github.com/MarvinLeRouge/Stamped/security/advisories/new) of this repository and click "Report a vulnerability". This keeps the report private until a fix is available.

This project is maintained by a single developer, so response times are best-effort rather than guaranteed on an SLA.

## Scope

In scope: the backend API (`backend/`), the frontend application (`frontend/`), the CLI (`stamped start` / `stamped index` / `stamped status`), and how the app reads local photo/GPX files and stores data in `data/`.

Out of scope: third-party services the application calls at import time (OSM tile servers, OpenTopoData, Nominatim). Report issues with those services directly to their maintainers.

## Notes specific to a local-first app

Stamped has no authentication, no accounts, and no network-facing attack surface beyond the three outbound calls described in the [Privacy](README.md#-privacy) section of the README (OSM tiles, OpenTopoData, Nominatim), all of which are read-only lookups, cached locally, and never carry photo content. The FastAPI server binds to `localhost` only and is intended to run on a single trusted machine, not to be exposed to a network.
