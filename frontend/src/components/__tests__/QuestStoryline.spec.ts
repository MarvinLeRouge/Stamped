import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuestStoryline from '../QuestStoryline.vue'
import { useQuestsStore } from '@/stores/quests'
import { useLightboxStore } from '@/stores/lightbox'
import api from '@/api'

vi.mock('@/api', () => ({ default: { get: vi.fn() } }))

const PHOTOS = [
  { id: 1, captured_at: '2024-06-01T08:10:00Z', thumb_status: 'done', is_orphan: false },
  { id: 2, captured_at: '2024-06-01T09:00:00Z', thumb_status: 'pending', is_orphan: false },
]

describe('QuestStoryline', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(api.get).mockResolvedValue({ data: PHOTOS })
    wrapper = mount(QuestStoryline, { attachTo: document.body })
  })

  afterEach(() => wrapper.unmount())

  it('renders nothing when no quest is selected', () => {
    expect(wrapper.find('.storyline').exists()).toBe(false)
  })

  it('renders the panel when a quest is selected', async () => {
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    expect(wrapper.find('.storyline').exists()).toBe(true)
  })

  it('shows loading while fetching', async () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    expect(wrapper.text()).toContain('Loading')
  })

  it('renders one item per photo', async () => {
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    expect(wrapper.findAll('.storyline__item')).toHaveLength(2)
  })

  it('shows numbered index badges', async () => {
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    const indices = wrapper.findAll('.storyline__index').map((el) => el.text())
    expect(indices).toEqual(['1', '2'])
  })

  it('renders thumbnail img for done photos', async () => {
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    const img = wrapper.find('img.storyline__thumb')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe('/api/photos/1/thumb')
  })

  it('renders pending placeholder for non-done photos', async () => {
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    expect(wrapper.find('.storyline__thumb--pending').exists()).toBe(true)
  })

  it('shows empty message when quest has no photos', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    expect(wrapper.text()).toContain('No photos')
  })

  it('clicking a done thumbnail opens the lightbox', async () => {
    const lightboxStore = useLightboxStore()
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    await wrapper.find('img.storyline__thumb').trigger('click')
    expect(lightboxStore.photoId).toBe(1)
  })

  it('hides the panel when quest is deselected', async () => {
    const store = useQuestsStore()
    store.selectedQuestId = 1
    await flushPromises()
    store.selectedQuestId = null
    await flushPromises()
    expect(wrapper.find('.storyline').exists()).toBe(false)
  })

  it('reloads photos when selected quest changes', async () => {
    const store = useQuestsStore()
    store.selectedQuestId = 1
    await flushPromises()
    vi.mocked(api.get).mockResolvedValue({ data: [PHOTOS[0]] })
    store.selectedQuestId = 2
    await flushPromises()
    expect(wrapper.findAll('.storyline__item')).toHaveLength(1)
  })
})
