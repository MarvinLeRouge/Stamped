import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useLayerStore } from '@/stores/layer'

describe('useLayerStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initialises with osm layer', () => {
    const store = useLayerStore()
    expect(store.activeLayerId).toBe('osm')
  })

  it('tileUrl contains active layer id', () => {
    const store = useLayerStore()
    expect(store.tileUrl).toContain('/osm/')
  })

  it('setLayer changes active layer', () => {
    const store = useLayerStore()
    store.setLayer('topo')
    expect(store.activeLayerId).toBe('topo')
    expect(store.tileUrl).toContain('/topo/')
  })

  it('activeLayer returns correct layer object', () => {
    const store = useLayerStore()
    store.setLayer('satellite')
    expect(store.activeLayer.label).toBe('Satellite')
  })
})
