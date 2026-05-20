<script setup lang="ts">
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

import L from 'leaflet'
import 'leaflet.markercluster'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { ref, watch } from 'vue'

import api from '@/api'
import { usePhotosStore } from '@/stores/photos'
import { useQuestsStore } from '@/stores/quests'
import { useLightboxStore } from '@/stores/lightbox'
import { usePlacementStore } from '@/stores/placement'
import { useHighlightStore } from '@/stores/highlight'

const TILE_URL = '/tiles/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
const CENTER: [number, number] = [46.8, 2.3]
const ZOOM = 5

const photosStore = usePhotosStore()
const questsStore = useQuestsStore()
const lightboxStore = useLightboxStore()
const placementStore = usePlacementStore()
const highlightStore = useHighlightStore()

const mapRef = ref<{ leafletObject: L.Map } | null>(null)
let clusterGroup: L.MarkerClusterGroup | null = null
let gpxPolylines: L.Polyline[] = []
const markerMap = new Map<number, L.Marker>()

function formatDate(capturedAt: string | null): string {
  if (!capturedAt) return ''
  const dt = new Date(capturedAt)
  return dt.toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function buildPopup(
  id: number,
  thumbStatus: string,
  capturedAt: string | null,
  index: number | null,
): string {
  const date = formatDate(capturedAt)
  const badge = index !== null ? `<span class="popup-index">${index}</span>` : ''
  if (thumbStatus === 'done') {
    return `<div class="photo-popup">
      ${badge}
      <img src="/api/photos/${id}/thumb" alt="photo" width="150" class="popup-thumb" style="cursor:pointer" />
      <p class="popup-date">${date}</p>
    </div>`
  }
  return `<div class="photo-popup">
    ${badge}
    <p class="popup-generating">Generating…</p>
    <p class="popup-date">${date}</p>
  </div>`
}

function refreshMarkers(): void {
  const map = mapRef.value?.leafletObject
  /* c8 ignore next */
  if (!map) return

  if (clusterGroup) {
    map.removeLayer(clusterGroup)
  }
  clusterGroup = L.markerClusterGroup()
  markerMap.clear()

  const geolocated = photosStore.photos.filter((p) => p.lat !== null && p.lon !== null)
  const inQuest = questsStore.selectedQuestId !== null

  geolocated.forEach((photo, i) => {
    const index = inQuest ? i + 1 : null
    const marker = L.marker([photo.lat as number, photo.lon as number])
    marker.bindPopup(buildPopup(photo.id, photo.thumb_status, photo.captured_at, index))
    marker.on('popupopen', () => {
      const img = marker.getPopup()?.getElement()?.querySelector('img.popup-thumb')
      if (img) {
        img.addEventListener('click', () => lightboxStore.open(photo.id), { once: true })
      }
    })
    marker.on('mouseover', () => highlightStore.highlight(photo.id))
    marker.on('mouseout', () => highlightStore.highlight(null))
    markerMap.set(photo.id, marker)
    clusterGroup!.addLayer(marker)
  })

  map.addLayer(clusterGroup)
}

async function onMapReady(): Promise<void> {
  const map = mapRef.value?.leafletObject
  /* c8 ignore next */
  if (!map) return

  map.on('click', async (e: L.LeafletMouseEvent) => {
    if (placementStore.placingPhotoId === null) return
    const { lat, lng } = e.latlng
    await api.patch(`/photos/${placementStore.placingPhotoId}`, { lat, lon: lng })
    placementStore.cancel()
    await loadVisiblePhotos()
  })

  map.on('moveend', loadVisiblePhotos)

  await Promise.all([photosStore.fetchPhotos(), questsStore.fetchQuests()])
  refreshMarkers()
  await refreshGpxTrace(questsStore.selectedQuestId)
}

async function refreshGpxTrace(questId: number | null): Promise<void> {
  const map = mapRef.value?.leafletObject
  /* c8 ignore next */
  if (!map) return

  for (const line of gpxPolylines) {
    map.removeLayer(line)
  }
  gpxPolylines = []

  if (questId === null) return

  try {
    const { data } = await api.get<number[][][]>(`/quests/${questId}/trackpoints`)
    for (const segment of data) {
      if (segment.length < 2) continue
      const line = L.polyline(segment as [number, number][], {
        color: '#e85d04',
        weight: 3,
        opacity: 0.8,
      })
      map.addLayer(line)
      gpxPolylines.push(line)
    }
  } catch {
    // no GPX for this quest — silent
  }
}

async function loadVisiblePhotos(): Promise<void> {
  const map = mapRef.value?.leafletObject
  /* c8 ignore next */
  if (!map) return

  const bounds = map.getBounds()
  const questId = questsStore.selectedQuestId

  await photosStore.fetchPhotos({
    lat_min: bounds.getSouth(),
    lat_max: bounds.getNorth(),
    lon_min: bounds.getWest(),
    lon_max: bounds.getEast(),
    ...(questId !== null ? { quest_id: questId } : {}),
  })
  refreshMarkers()
}

watch(
  () => highlightStore.hoveredPhotoId,
  (newId, oldId) => {
    if (oldId !== null) {
      markerMap.get(oldId)?.getElement()?.classList.remove('marker--highlighted')
    }
    if (newId !== null) {
      markerMap.get(newId)?.getElement()?.classList.add('marker--highlighted')
    }
  },
)

watch(
  () => placementStore.placingPhotoId,
  (id) => {
    const map = mapRef.value?.leafletObject
    if (!map) return
    map.getContainer().style.cursor = id !== null ? 'crosshair' : ''
  },
)

watch(
  () => questsStore.selectedQuestId,
  async (id) => {
    await refreshGpxTrace(id)
    const map = mapRef.value?.leafletObject
    if (id !== null && map) {
      const quest = questsStore.quests.find((q) => q.id === id)
      if (
        quest &&
        quest.bbox_lat_min !== null &&
        quest.bbox_lat_max !== null &&
        quest.bbox_lon_min !== null &&
        quest.bbox_lon_max !== null
      ) {
        map.fitBounds(
          [
            [quest.bbox_lat_min, quest.bbox_lon_min],
            [quest.bbox_lat_max, quest.bbox_lon_max],
          ],
          { padding: [40, 40] },
        )
        return
      }
    }
    await loadVisiblePhotos()
  },
)
</script>

<template>
  <l-map ref="mapRef" :zoom="ZOOM" :center="CENTER" class="map" @ready="onMapReady">
    <l-tile-layer :url="TILE_URL" :attribution="TILE_ATTRIBUTION" layer-type="base" />
  </l-map>
</template>

<style scoped>
.map {
  height: 100%;
  width: 100%;
}
</style>

<style>
.photo-popup {
  position: relative;
}
.photo-popup img {
  display: block;
  border-radius: 4px;
}
.popup-index {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  line-height: 1.4;
}
.popup-date {
  margin-top: 4px;
  font-size: 0.8rem;
  color: #555;
  text-align: center;
}
.marker--highlighted {
  filter: hue-rotate(160deg) brightness(1.3) drop-shadow(0 0 4px #e85d04);
  z-index: 9999 !important;
}
.popup-generating {
  width: 150px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 4px;
  color: #888;
  font-size: 0.8rem;
}
</style>
