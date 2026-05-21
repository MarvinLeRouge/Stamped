import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export type LayerId = 'osm' | 'topo' | 'satellite'

export interface Layer {
  id: LayerId
  label: string
  attribution: string
}

export const LAYERS: Layer[] = [
  {
    id: 'osm',
    label: 'OSM',
    attribution:
      '© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
  },
  {
    id: 'topo',
    label: 'Topo',
    attribution:
      '© <a href="https://opentopomap.org" target="_blank">OpenTopoMap</a> · © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
  },
  {
    id: 'satellite',
    label: 'Satellite',
    attribution:
      'Tiles © <a href="https://www.esri.com" target="_blank">Esri</a> — Source: Esri, USGS, NOAA',
  },
]

export const useLayerStore = defineStore('layer', () => {
  const activeLayerId = ref<LayerId>('osm')

  const activeLayer = computed(() => LAYERS.find((l) => l.id === activeLayerId.value)!)

  const tileUrl = computed(() => `/api/tiles/${activeLayerId.value}/{z}/{x}/{y}`)

  function setLayer(id: LayerId): void {
    activeLayerId.value = id
  }

  return { activeLayerId, activeLayer, tileUrl, setLayer }
})
