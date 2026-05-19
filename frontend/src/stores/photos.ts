import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '@/api'

export interface Photo {
  id: number
  lat: number | null
  lon: number | null
  captured_at: string | null
  thumb_status: string
  quest_id: number | null
  is_orphan: boolean
}

export interface PhotoFilters {
  lat_min?: number
  lat_max?: number
  lon_min?: number
  lon_max?: number
  date_from?: string
  date_to?: string
  quest_id?: number | null
  orphan?: boolean
}

export const usePhotosStore = defineStore('photos', () => {
  const photos = ref<Photo[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPhotos(filters: PhotoFilters = {}): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, v]) => v !== undefined && v !== null),
      )
      const { data } = await api.get<Photo[]>('/photos', { params })
      photos.value = data
    } catch {
      error.value = 'Failed to load photos'
    } finally {
      loading.value = false
    }
  }

  return { photos, loading, error, fetchPhotos }
})
