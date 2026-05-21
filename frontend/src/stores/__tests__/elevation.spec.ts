import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useElevationStore } from '@/stores/elevation'

describe('useElevationStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initialises hidden with no points', () => {
    const store = useElevationStore()
    expect(store.visible).toBe(false)
    expect(store.points).toHaveLength(0)
  })

  it('toggle shows the panel', () => {
    const store = useElevationStore()
    store.toggle()
    expect(store.visible).toBe(true)
  })

  it('toggle twice hides the panel', () => {
    const store = useElevationStore()
    store.toggle()
    store.toggle()
    expect(store.visible).toBe(false)
  })

  it('setPoints stores elevation data', () => {
    const store = useElevationStore()
    store.setPoints([{ d: 0, alt: 100, t: '2024-01-01T08:00:00Z' }])
    expect(store.points).toHaveLength(1)
    expect(store.points[0]!.alt).toBe(100)
  })
})
