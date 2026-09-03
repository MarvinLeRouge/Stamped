🇫🇷 Version française | [🇬🇧 English version](frontend_developer_guide.md)

---

# Guide développeur frontend - Stamped

Voir [architecture frontend](../architecture/frontend_architecture.fr.md) pour la structure et la gestion d'état. Ce guide couvre les conventions au quotidien pour travailler dans `frontend/src/`.

## Technologies

- Vue 3, Composition API avec `<script setup>` uniquement (pas d'Options API)
- Vite, TypeScript
- Pinia pour l'état
- Axios pour le HTTP, Leaflet pour la carte

## Ajouter un store

Chaque store Pinia gère un seul domaine (photos, quests, status, layer, lightbox, placement, highlight, elevation). Utiliser `defineStore` avec la syntaxe `setup` (fonctions retournant refs/computed/actions), en suivant le modèle des stores existants dans `frontend/src/stores/`. Les fonctions `fetch`/actions d'un store appellent `api/index.ts` directement - il n'y a pas de couche de modules API séparée par ressource à traverser.

## Appeler l'API

Il existe une instance Axios unique dans `frontend/src/api/index.ts`, base URL `/api`. Les composants n'appellent jamais Axios directement ; ils appellent les actions des stores, et les stores appellent l'instance partagée. Ajouter les nouveaux appels d'endpoint comme actions de store, pas comme appels ad hoc dans les composants.

## Fraîcheur des données

Les stores récupèrent les données au montage et les re-récupèrent explicitement après une action de mutation (ex. après suppression d'une photo, re-fetch du store status) plutôt que de rester à jour via une connexion persistante. Le backend expose un endpoint SSE (`GET /api/events`) pour la progression de l'import/des thumbnails, mais le frontend ne le consomme pas actuellement - voir [architecture frontend](../architecture/frontend_architecture.fr.md) et [docs/operations.md](../operations.fr.md).

## Synchronisation carte / storyline

`stores/highlight.ts` est la source de vérité partagée pour l'état de survol entre `MapView`, `QuestStoryline` et `ElevationPanel`. Pour un nouveau composant participant à cette synchronisation, lire/écrire via ce store plutôt que de faire passer l'état de survol en props entre composants frères.

## Conventions de composant

- Un composant par fichier, `PascalCase.vue`, dans `frontend/src/components/`.
- Aucun dossier `composables/` n'existe - l'état réactif partagé va dans un store Pinia, pas dans un composable custom, sauf s'il est réellement local à un seul arbre de composants.
- Le CSS est scoped par composant (`<style scoped>`) ; voir [docs/design-system.md](../design-system.fr.md) pour les conventions de couleur/espacement/nommage réellement suivies.

## Build et serveur de dev

```bash
npm run dev     # serveur de dev Vite, fait proxy de /api vers 127.0.0.1:8421
npm run build    # vue-tsc --build (vérification de types) et vite build en parallèle (run-p)
```

## Tests

```bash
make test-frontend
# ou
cd frontend && npm run test:unit -- --coverage
```

- Vitest, environnement JSDOM, Vue Test Utils.
- Tester les stores Pinia isolément (mocker la couche API, pas le store).
- Couvrir les interactions de composant : événements carte, mode placement, lightbox, flux renommer/supprimer/placer de la storyline.

## Lint

```bash
make lint-frontend   # eslint, prettier --check, vue-tsc
make format            # eslint --fix, prettier --write
```

Un hook pre-push exécute la vérification de types `vue-tsc` localement avant tout push.
