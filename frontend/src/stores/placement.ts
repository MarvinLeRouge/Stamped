import { defineStore } from 'pinia'
import { ref } from 'vue'

export const usePlacementStore = defineStore('placement', () => {
  const placingPhotoId = ref<number | null>(null)

  function startPlacing(photoId: number): void {
    placingPhotoId.value = photoId
  }

  function cancel(): void {
    placingPhotoId.value = null
  }

  return { placingPhotoId, startPlacing, cancel }
})
