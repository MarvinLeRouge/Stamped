import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ElevationPoint {
  d: number
  alt: number
  t: string
}

export const useElevationStore = defineStore('elevation', () => {
  const visible = ref(false)
  const points = ref<ElevationPoint[]>([])
  const loading = ref(false)

  function toggle(): void {
    visible.value = !visible.value
  }

  function setPoints(data: ElevationPoint[]): void {
    points.value = data
  }

  function setLoading(v: boolean): void {
    loading.value = v
  }

  return { visible, points, loading, toggle, setPoints, setLoading }
})
