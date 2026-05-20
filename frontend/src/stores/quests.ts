import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '@/api'

export interface Quest {
  id: number
  name: string | null
  auto_name: string
  started_at: string | null
  ended_at: string | null
  photo_count: number
  has_gpx: boolean
  bbox_lat_min: number | null
  bbox_lat_max: number | null
  bbox_lon_min: number | null
  bbox_lon_max: number | null
}

export const useQuestsStore = defineStore('quests', () => {
  const quests = ref<Quest[]>([])
  const selectedQuestId = ref<number | null>(null)
  const showUnquested = ref(false)
  const showAllPhotos = ref(false)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchQuests(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<Quest[]>('/quests')
      quests.value = data
    } catch {
      error.value = 'Failed to load quests'
    } finally {
      loading.value = false
    }
  }

  async function renameQuest(id: number, name: string | null): Promise<void> {
    const { data } = await api.patch<Quest>(`/quests/${id}`, { name })
    const idx = quests.value.findIndex((q) => q.id === id)
    if (idx !== -1) quests.value[idx] = data
  }

  function selectQuest(id: number | null): void {
    selectedQuestId.value = id
    if (id !== null) {
      showUnquested.value = false
      showAllPhotos.value = false
    }
  }

  function toggleUnquested(): void {
    showUnquested.value = !showUnquested.value
    if (showUnquested.value) {
      selectedQuestId.value = null
      showAllPhotos.value = false
    }
  }

  function toggleAllPhotos(): void {
    showAllPhotos.value = !showAllPhotos.value
    if (showAllPhotos.value) {
      selectedQuestId.value = null
      showUnquested.value = false
    }
  }

  return {
    quests,
    selectedQuestId,
    showUnquested,
    showAllPhotos,
    loading,
    error,
    fetchQuests,
    renameQuest,
    selectQuest,
    toggleUnquested,
    toggleAllPhotos,
  }
})
