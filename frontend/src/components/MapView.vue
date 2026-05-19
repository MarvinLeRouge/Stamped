<script setup lang="ts">
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'

import L from 'leaflet'
import 'leaflet.markercluster'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import { ref, watch } from 'vue'

import { usePhotosStore } from '@/stores/photos'
import { useQuestsStore } from '@/stores/quests'

const TILE_URL = '/tiles/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
const CENTER: [number, number] = [46.8, 2.3]
const ZOOM = 5

const photosStore = usePhotosStore()
const questsStore = useQuestsStore()

const mapRef = ref<{ leafletObject: L.Map } | null>(null)
let clusterGroup: L.MarkerClusterGroup | null = null

function buildPopup(id: number, thumbStatus: string, capturedAt: string | null): string {
  const date = capturedAt ? capturedAt.slice(0, 10) : ''
  if (thumbStatus === 'done') {
    return `<div class="photo-popup">
      <img src="/api/photos/${id}/thumb" alt="photo" width="150" />
      <p class="popup-date">${date}</p>
    </div>`
  }
  return `<div class="photo-popup">
    <p class="popup-generating">Generating…</p>
    <p class="popup-date">${date}</p>
  </div>`
}

function refreshMarkers(): void {
  const map = mapRef.value?.leafletObject
  if (!map) return

  if (clusterGroup) {
    map.removeLayer(clusterGroup)
  }
  clusterGroup = L.markerClusterGroup()

  for (const photo of photosStore.photos) {
    if (photo.lat === null || photo.lon === null) continue
    const marker = L.marker([photo.lat, photo.lon])
    marker.bindPopup(buildPopup(photo.id, photo.thumb_status, photo.captured_at))
    clusterGroup.addLayer(marker)
  }

  map.addLayer(clusterGroup)
}

async function onMapReady(): Promise<void> {
  const map = mapRef.value?.leafletObject
  if (!map) return

  map.on('moveend', loadVisiblePhotos)

  await Promise.all([photosStore.fetchPhotos(), questsStore.fetchQuests()])
  refreshMarkers()
}

async function loadVisiblePhotos(): Promise<void> {
  const map = mapRef.value?.leafletObject
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

watch(() => questsStore.selectedQuestId, loadVisiblePhotos)
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
.photo-popup img {
  display: block;
  border-radius: 4px;
}
.popup-date {
  margin-top: 4px;
  font-size: 0.75rem;
  color: #555;
  text-align: center;
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
