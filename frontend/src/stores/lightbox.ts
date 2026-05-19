import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLightboxStore = defineStore('lightbox', () => {
  const photoId = ref<number | null>(null)

  function open(id: number): void {
    photoId.value = id
  }

  function close(): void {
    photoId.value = null
  }

  return { photoId, open, close }
})
