import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useHighlightStore = defineStore('highlight', () => {
  const hoveredPhotoId = ref<number | null>(null)

  function highlight(id: number | null): void {
    hoveredPhotoId.value = id
  }

  return { hoveredPhotoId, highlight }
})
