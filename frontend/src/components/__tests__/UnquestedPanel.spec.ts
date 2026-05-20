import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import UnquestedPanel from '../UnquestedPanel.vue'
import { useQuestsStore } from '@/stores/quests'
import { usePlacementStore } from '@/stores/placement'
import api from '@/api'

vi.mock('@/api', () => ({ default: { get: vi.fn(), delete: vi.fn() } }))

const PHOTOS = [
  { id: 10, captured_at: '2024-05-01T08:00:00Z', thumb_status: 'done', is_orphan: true },
  { id: 11, captured_at: '2024-05-02T09:00:00Z', thumb_status: 'pending', is_orphan: true },
]

describe('UnquestedPanel', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(api.get).mockResolvedValue({ data: PHOTOS })
    wrapper = mount(UnquestedPanel, { attachTo: document.body })
  })

  afterEach(() => wrapper.unmount())

  it('renders nothing when showUnquested is false', () => {
    expect(wrapper.find('.unquested').exists()).toBe(false)
  })

  it('renders panel when showUnquested is true', async () => {
    useQuestsStore().showUnquested = true
    await flushPromises()
    expect(wrapper.find('.unquested').exists()).toBe(true)
  })

  it('shows loading while fetching', async () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    useQuestsStore().showUnquested = true
    await flushPromises()
    expect(wrapper.text()).toContain('Loading')
  })

  it('renders one item per photo', async () => {
    useQuestsStore().showUnquested = true
    await flushPromises()
    expect(wrapper.findAll('.unquested__item')).toHaveLength(2)
  })

  it('shows thumbnail for done photos', async () => {
    useQuestsStore().showUnquested = true
    await flushPromises()
    expect(wrapper.find('img.unquested__thumb').attributes('src')).toBe('/api/photos/10/thumb')
  })

  it('shows empty message when no photos', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    useQuestsStore().showUnquested = true
    await flushPromises()
    expect(wrapper.text()).toContain('No photos')
  })

  it('clicking thumbnail opens lightbox', async () => {
    const { useLightboxStore } = await import('@/stores/lightbox')
    const lightboxStore = useLightboxStore()
    useQuestsStore().showUnquested = true
    await flushPromises()
    await wrapper.find('img.unquested__thumb').trigger('click')
    expect(lightboxStore.photoId).toBe(PHOTOS[0]!.id)
  })

  it('clicking place button activates placement mode', async () => {
    useQuestsStore().showUnquested = true
    await flushPromises()
    await wrapper.find('.unquested__action-btn--pin').trigger('click')
    expect(usePlacementStore().placingPhotoId).toBe(PHOTOS[0]!.id)
  })

  it('clicking delete removes photo from list', async () => {
    vi.mocked(api.delete).mockResolvedValue({})
    useQuestsStore().showUnquested = true
    await flushPromises()
    await wrapper.find('.unquested__action-btn--danger').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.unquested__item')).toHaveLength(1)
  })

  it('hiding panel clears placement mode', async () => {
    const store = useQuestsStore()
    const placementStore = usePlacementStore()
    store.showUnquested = true
    await flushPromises()
    placementStore.startPlacing(10)
    store.showUnquested = false
    await flushPromises()
    expect(placementStore.placingPhotoId).toBeNull()
  })
})
