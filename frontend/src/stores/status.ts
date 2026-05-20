import { defineStore } from 'pinia'
import { ref } from 'vue'

import api from '@/api'

export interface SystemStatus {
  photos_total: number
  thumbs_done: number
  thumbs_pending: number
  orphans: number
  unquested: number
  gpx_files: number
  quests: number
  last_index_at: string | null
}

export const useStatusStore = defineStore('status', () => {
  const status = ref<SystemStatus | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<SystemStatus>('/status')
      status.value = data
    } catch {
      error.value = 'Server unreachable'
    } finally {
      loading.value = false
    }
  }

  return { status, loading, error, fetch }
})
