import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { usePlacementStore } from '@/stores/placement'

describe('usePlacementStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initialises with no photo being placed', () => {
    expect(usePlacementStore().placingPhotoId).toBeNull()
  })

  it('startPlacing sets the photo id', () => {
    const store = usePlacementStore()
    store.startPlacing(42)
    expect(store.placingPhotoId).toBe(42)
  })

  it('cancel clears the photo id', () => {
    const store = usePlacementStore()
    store.startPlacing(42)
    store.cancel()
    expect(store.placingPhotoId).toBeNull()
  })
})
