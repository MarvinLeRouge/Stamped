[🇫🇷 Version française](frontend_developer_guide.fr.md) | 🇬🇧 English version

---

# Frontend Developer Guide - Stamped

See [frontend architecture](../architecture/frontend_architecture.md) for the layout and state management overview. This guide covers day-to-day conventions for working in `frontend/src/`.

## Technologies

- Vue 3, Composition API with `<script setup>` only (no Options API)
- Vite, TypeScript
- Pinia for state
- Axios for HTTP, Leaflet for the map

## Adding a store

Each Pinia store owns exactly one domain concern (photos, quests, status, layer, lightbox, placement, highlight, elevation). Use `defineStore` with the `setup` syntax (functions returning refs/computed/actions), matching the existing stores in `frontend/src/stores/`. A store's `fetch`/action functions call `api/index.ts` directly - there is no separate per-resource API module layer to route through.

## Calling the API

There is a single Axios instance in `frontend/src/api/index.ts`, base URL `/api`. Components never call Axios directly; they call store actions, and stores call the shared instance. Add new endpoint calls as store actions, not as ad hoc calls inside components.

## Data freshness

Stores fetch on mount and re-fetch explicitly after a mutating action (e.g. after a photo delete, re-fetch the status store) rather than staying live via a persistent connection. The backend exposes an SSE endpoint (`GET /api/events`) for import/thumbnail progress, but the frontend does not currently consume it - see [frontend architecture](../architecture/frontend_architecture.md) and [docs/operations.md](../operations.md).

## Map / storyline synchronisation

`stores/highlight.ts` is the shared source of truth for hover state between `MapView`, `QuestStoryline` and `ElevationPanel`. When adding a component that needs to participate in this synchronisation, read/write through this store rather than passing hover state as props between siblings.

## Component conventions

- One component per file, `PascalCase.vue`, in `frontend/src/components/`.
- No `composables/` directory exists - shared reactive state belongs in a Pinia store, not a custom composable, unless it is genuinely local to a single component tree.
- CSS is scoped per component (`<style scoped>`); see [docs/design-system.md](../design-system.md) for the color/spacing/naming conventions actually followed.

## Build and dev server

```bash
npm run dev     # Vite dev server, proxies /api to 127.0.0.1:8421
npm run build    # vue-tsc --build (type-check) and vite build in parallel (run-p)
```

## Testing

```bash
make test-frontend
# or
cd frontend && npm run test:unit -- --coverage
```

- Vitest, JSDOM environment, Vue Test Utils.
- Test Pinia stores in isolation (mock the API layer, not the store).
- Cover component interactions: map events, placement mode, lightbox, storyline rename/delete/place flow.

## Linting

```bash
make lint-frontend   # eslint, prettier --check, vue-tsc
make format            # eslint --fix, prettier --write
```

A pre-push hook runs `vue-tsc` type-checking locally before any push.
