🇫🇷 Version française | [🇬🇧 English version](api_endpoints.md)

---

# Référence API - Stamped

URL de base : `http://127.0.0.1:8421/api` (l'endpoint SSE et le proxy de tuiles vivent hors du préfixe `/api` uniquement pour la route legacy des tuiles, voir plus bas).

Ceci est une référence statique et commitée, maintenue à jour manuellement. La doc interactive live (Swagger UI) n'est accessible qu'une fois l'app installée et lancée, sur `http://127.0.0.1:8421/docs` - ce fichier existe pour permettre de consulter la surface de l'API sans rien installer.

## Statut

### `GET /api/status`

Retourne des compteurs agrégés, calculés en direct (non mis en cache, voir [ADR 0010](../adr/0010-live-count-vs-cached-orphan-counter.md)).

```json
{
  "photos_total": 0,
  "thumbs_done": 0,
  "thumbs_pending": 0,
  "orphans": 0,
  "unquested": 0,
  "gpx_files": 0,
  "quests": 0,
  "last_index_at": null
}
```

## Quests

### `GET /api/quests`

Toutes les quests triées par `started_at`. Chaque élément :

```json
{
  "id": 1,
  "name": null,
  "auto_name": "2024-08-12",
  "started_at": "2024-08-12T08:00:00Z",
  "ended_at": "2024-08-12T17:00:00Z",
  "photo_count": 42,
  "has_gpx": true,
  "bbox_lat_min": 45.1,
  "bbox_lat_max": 45.4,
  "bbox_lon_min": 6.1,
  "bbox_lon_max": 6.5
}
```

### `PATCH /api/quests/{quest_id}`

Corps : `{"name": "Nouveau nom"}` (ou `null`/vide pour revenir à `auto_name`). Retourne la quest mise à jour (même forme que ci-dessus). `404` si la quest n'existe pas.

### `GET /api/quests/{quest_id}/photos`

Liste chronologique des photos d'une quest :

```json
[{"id": 1, "lat": 45.2, "lon": 6.3, "captured_at": "2024-08-12T09:00:00Z", "thumb_status": "done", "is_orphan": false}]
```

### `GET /api/quests/{quest_id}/trackpoints`

Trackpoints GPX groupés par fichier, un segment (liste de paires `[lat, lon]`) par fichier GPX :

```json
[[[45.2, 6.3], [45.21, 6.31]], [[45.3, 6.4]]]
```

### `GET /api/quests/{quest_id}/gpx`

Télécharge la trace GPX de la quest (`application/gpx+xml`). Si la quest n'a qu'un seul fichier GPX source, ce fichier est servi tel quel ; si elle en a plusieurs, ils sont fusionnés dans un document GPX généré. `404` si la quest n'a pas de fichier GPX.

### `POST /api/quests/{quest_id}/place`

Place en masse toutes les photos orphelines d'une quest. Corps `{}` utilise le point GPS médian chronologique (voir [ADR 0012](../adr/0012-chronological-median-orphan-placement.md)) ; corps `{"lat": ..., "lon": ...}` utilise des coordonnées explicites à la place.

```json
{"placed": 5, "lat": 45.2, "lon": 6.3}
```

`422` s'il n'existe aucun point GPS de référence pour la quest et qu'aucune coordonnée explicite n'a été fournie.

### `GET /api/quests/{quest_id}/elevation`

Points du profil d'élévation le long des trackpoints GPX de la quest, distance cumulée en mètres, horodatages ajustés par `STAMPED_CAMERA_UTC_OFFSET_HOURS` (voir [ADR 0013](../adr/0013-camera-utc-offset-reconciliation.md)) :

```json
[{"d": 0.0, "alt": 1200.5, "t": "2024-08-12T09:00:00Z"}]
```

## Photos

### `GET /api/photos`

Paramètres de requête (tous optionnels) : `lat_min`, `lat_max`, `lon_min`, `lon_max` (zone), `date_from`, `date_to`, `quest_id`, `orphan` (bool), `no_quest` (bool), `limit` (1-1000, défaut 500), `offset`.

```json
[{"id": 1, "lat": 45.2, "lon": 6.3, "captured_at": "2024-08-12T09:00:00Z", "thumb_status": "done", "quest_id": 1, "is_orphan": false}]
```

### `PATCH /api/photos/{photo_id}`

Corps : `{"lat": 45.2, "lon": 6.3}`. Fixe les coordonnées et retire le flag orphelin. Retourne la photo mise à jour. `404` si absente.

### `DELETE /api/photos/{photo_id}`

Retire l'enregistrement DB, supprime le fichier de thumbnail généré s'il existe, et ajoute le hash SHA-256 de la photo à `deleted_photos` pour empêcher sa réimportation (voir [ADR 0011](../adr/0011-photo-deletion-db-only.md)). Le fichier original n'est jamais touché. `204` en cas de succès, `404` si absente.

### `GET /api/photos/{photo_id}/thumb`

Sert la thumbnail générée (`image/jpeg`) si prête. Retourne `202` avec l'en-tête `X-Thumb-Status` si la thumbnail est encore en attente.

### `GET /api/photos/{photo_id}/original`

Sert le fichier photo original (`image/jpeg`), lu directement depuis son chemin sur disque.

### `POST /api/photos/{photo_id}/thumb/priority`

Fait passer la génération de la thumbnail de la photo devant la file d'attente en arrière-plan. Retourne `{"status": "queued"}`.

## Import

### `POST /api/import`

> Voir [docs/operations.md](../operations.fr.md) - c'est actuellement le seul moyen fonctionnel de déclencher un import ; la commande CLI `stamped index` est un stub.

Corps : `{"path": "/chemin/absolu/vers/photos"}`. `400` si le chemin n'existe pas. Démarre le pipeline d'import en tâche de fond et retourne immédiatement (`202`) :

```json
{"job_id": "b3f1...", "status": "started"}
```

### `GET /api/import/{job_id}`

Interroger la progression :

```json
{
  "job_id": "b3f1...",
  "status": "running",
  "phase": "gpx",
  "progress": 0.3,
  "indexed": 120,
  "total": 0,
  "errors": 0,
  "started_at": "2024-08-12T09:00:00Z",
  "finished_at": null
}
```

`status` vaut `running`, `done` ou `error`. `phase` vaut `import`, `gpx`, `clustering`, `interpolation`, `elevation`, `thumbnails` ou `done`. `404` si l'ID de job est inconnu (l'état du job est en mémoire, perdu au redémarrage du serveur).

### `POST /api/reindex`

Corps : `{"confirm": true}` (requis, sinon `400`). Efface photos, quests, fichiers GPX et cache de géocodage, puis retourne `{"status": "cleared"}`. Ne touche pas aux fichiers originaux.

## Recherche

### `GET /api/search/geocode?q=...`

Fait proxy vers le géocodage Nominatim (`q` longueur minimale 2), met en cache les résultats dans `geocode_cache`. Les hits de cache évitent tout appel réseau.

```json
[{"display_name": "Chamonix, France", "lat": 45.9, "lon": 6.87, "bbox_lat_min": 45.8, "bbox_lat_max": 46.0, "bbox_lon_min": 6.7, "bbox_lon_max": 7.0}]
```

Les champs de bounding box sont `null` sur les hits de cache (non stockés dans la table de cache).

## Tuiles

### `GET /api/tiles/{layer}/{z}/{x}/{y}`

Fait proxy et met en cache les tuiles de carte pour `layer` parmi `osm`, `topo`, `satellite` (voir [ADR 0015](../adr/0015-osm-layer-alternatives-per-layer-cache.md)). Servie depuis le cache filesystem si présente, sinon récupérée depuis le serveur de tuiles amont et mise en cache. `404` pour une couche inconnue, `502` si la récupération amont échoue.

### `GET /api/tiles/{z}/{x}/{y}.png`

Route legacy, redirige vers `/api/tiles/osm/{z}/{x}/{y}`.

## Événements temps réel

### `GET /api/events`

Flux Server-Sent Events (`text/event-stream`). Publie des événements `import_progress` pendant le pipeline d'import (mêmes champs que la réponse de polling du statut de job) et `import_error` en cas d'échec. Non consommé actuellement par le frontend, voir [architecture frontend](../architecture/frontend_architecture.fr.md).
