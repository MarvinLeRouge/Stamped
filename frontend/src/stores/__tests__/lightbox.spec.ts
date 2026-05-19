import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useLightboxStore } from '@/stores/lightbox'

describe('useLightboxStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initialises with no photo', () => {
    expect(useLightboxStore().photoId).toBeNull()
  })

  it('open sets photoId', () => {
    const store = useLightboxStore()
    store.open(42)
    expect(store.photoId).toBe(42)
  })

  it('close clears photoId', () => {
    const store = useLightboxStore()
    store.open(42)
    store.close()
    expect(store.photoId).toBeNull()
  })
})
