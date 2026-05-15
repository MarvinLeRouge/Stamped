<script setup lang="ts">
import 'leaflet/dist/leaflet.css'
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'

const TILE_URL = '/tiles/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION =
  '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>'
const CENTER: [number, number] = [46.8, 2.3]
const ZOOM = 5
</script>

<template>
  <l-map :zoom="ZOOM" :center="CENTER" class="map">
    <l-tile-layer :url="TILE_URL" :attribution="TILE_ATTRIBUTION" layer-type="base" />
  </l-map>
</template>

<style scoped>
.map {
  height: 100%;
  width: 100%;
}
</style>
