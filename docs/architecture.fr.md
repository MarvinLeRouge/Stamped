🇫🇷 Version française | [🇬🇧 English version](architecture.md)

---

# Architecture - Stamped

> Référence technique publique. Voir [architecture backend](architecture/backend_architecture.fr.md) et [architecture frontend](architecture/frontend_architecture.fr.md) pour les détails d'implémentation.

## Vue d'ensemble

Stamped est une application web locale à deux processus :

- **Backend** - FastAPI (Python) sur `127.0.0.1:8421`. Gère l'indexation des fichiers, l'extraction EXIF, le parsing GPX, la détection des quests, la génération des thumbnails, et sert l'API REST.
- **Frontend** - SPA Vue 3 + Vite. Servie par le backend en production, serveur de dev Vite en développement. Affiche la carte Leaflet, la liste des quests, la storyline et le tableau de bord d'import.

Les deux processus communiquent via l'API REST. La progression de l'import et des thumbnails est poussée par le backend via Server-Sent Events (non consommée actuellement par le frontend, voir [architecture frontend](architecture/frontend_architecture.fr.md)).

## Structure du projet

```
stamped/
├── backend/
│   ├── stamped/
│   │   ├── api/          # routes FastAPI
│   │   ├── workers/      # sous-processus CPU-bound
│   │   ├── services/     # logique métier
│   │   └── core/         # db, config, events, fs
│   └── tests/
├── frontend/
│   └── src/
├── data/                 # runtime, gitignored
├── migrations/           # scripts SQL versionnés
└── docs/
    ├── architecture/      # architecture backend/frontend
    ├── adr/               # décisions d'architecture
    ├── api/                # référence API
    └── guides/              # guides développeur/utilisateur
```

## Pour aller plus loin

- [Architecture backend](architecture/backend_architecture.fr.md)
- [Architecture frontend](architecture/frontend_architecture.fr.md)
- [Référence API](api/api_endpoints.fr.md)
- [Registre des décisions d'architecture](adr/README.md)
- [Contexte produit](product-context.fr.md)
- [Opérations](operations.fr.md)
