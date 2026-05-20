import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useHighlightStore } from '@/stores/highlight'

describe('useHighlightStore', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('initialises with no highlighted photo', () => {
    expect(useHighlightStore().hoveredPhotoId).toBeNull()
  })

  it('highlight sets hoveredPhotoId', () => {
    const store = useHighlightStore()
    store.highlight(7)
    expect(store.hoveredPhotoId).toBe(7)
  })

  it('highlight with null clears hoveredPhotoId', () => {
    const store = useHighlightStore()
    store.highlight(7)
    store.highlight(null)
    expect(store.hoveredPhotoId).toBeNull()
  })
})
