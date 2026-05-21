import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useHighlightStore = defineStore('highlight', () => {
  const hoveredPhotoId = ref<number | null>(null)
  const hoveredTimestamp = ref<string | null>(null)

  function highlight(id: number | null, timestamp: string | null = null): void {
    hoveredPhotoId.value = id
    hoveredTimestamp.value = timestamp
  }

  return { hoveredPhotoId, hoveredTimestamp, highlight }
})
