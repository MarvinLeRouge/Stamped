import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuestStoryline from '../QuestStoryline.vue'
import { useQuestsStore } from '@/stores/quests'
import { useLightboxStore } from '@/stores/lightbox'
import { usePlacementStore } from '@/stores/placement'
import { useStatusStore } from '@/stores/status'
import api from '@/api'

vi.mock('@/api', () => ({ default: { get: vi.fn(), patch: vi.fn(), delete: vi.fn() } }))

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

  it('clicking delete button removes photo from list', async () => {
    vi.mocked(api.delete).mockResolvedValue({})
    const store = useQuestsStore()
    const statusStore = useStatusStore()
    vi.spyOn(store, 'fetchQuests').mockResolvedValue()
    vi.spyOn(statusStore, 'fetch').mockResolvedValue()
    store.selectedQuestId = 1
    await flushPromises()
    await wrapper.find('.storyline__action-btn--danger').trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.storyline__item')).toHaveLength(1)
    expect(store.fetchQuests).toHaveBeenCalled()
    expect(statusStore.fetch).toHaveBeenCalled()
  })

  it('clicking place button activates placement mode', async () => {
    const placementStore = usePlacementStore()
    useQuestsStore().selectedQuestId = 1
    await flushPromises()
    await wrapper.find('.storyline__action-btn').trigger('click')
    expect(placementStore.placingPhotoId).toBe(PHOTOS[0]!.id)
  })

  it('deselecting quest cancels placement mode', async () => {
    const store = useQuestsStore()
    const placementStore = usePlacementStore()
    store.selectedQuestId = 1
    await flushPromises()
    placementStore.startPlacing(PHOTOS[0]!.id)
    store.selectedQuestId = null
    await flushPromises()
    expect(placementStore.placingPhotoId).toBeNull()
  })
})

// ── Rename ─────────────────────────────────────────────────────────────────

describe('QuestStoryline — rename', () => {
  const QUEST = {
    id: 1,
    name: null,
    auto_name: 'Quest 2024-06-01',
    started_at: null,
    ended_at: null,
    photo_count: 0,
    has_gpx: false,
    bbox_lat_min: null,
    bbox_lat_max: null,
    bbox_lon_min: null,
    bbox_lon_max: null,
  }

  let wrapper: ReturnType<typeof mount>
  let store: ReturnType<typeof useQuestsStore>

  beforeEach(async () => {
    setActivePinia(createPinia())
    store = useQuestsStore()
    store.quests = [{ ...QUEST }]
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    vi.mocked(api.patch).mockResolvedValue({ data: { ...QUEST, name: 'Mon aventure' } })
    wrapper = mount(QuestStoryline, { attachTo: document.body })
    store.selectedQuestId = 1
    await flushPromises()
  })

  afterEach(() => wrapper.unmount())

  it('shows auto_name in the header when name is null', () => {
    expect(wrapper.find('.storyline__title').text()).toBe('Quest 2024-06-01')
  })

  it('shows custom name when set', async () => {
    store.quests = [{ ...QUEST, name: 'Mon aventure' }]
    await flushPromises()
    expect(wrapper.find('.storyline__title').text()).toBe('Mon aventure')
  })

  it('clicking the edit button shows the input', async () => {
    await wrapper.find('.storyline__edit-btn').trigger('click')
    expect(wrapper.find('.storyline__name-input').exists()).toBe(true)
    expect(wrapper.find('.storyline__title').exists()).toBe(false)
  })

  it('input is pre-filled with current name', async () => {
    store.quests = [{ ...QUEST, name: 'Existing' }]
    await flushPromises()
    await wrapper.find('.storyline__edit-btn').trigger('click')
    expect((wrapper.find('.storyline__name-input').element as HTMLInputElement).value).toBe(
      'Existing',
    )
  })

  it('Enter key commits the rename', async () => {
    vi.spyOn(store, 'renameQuest').mockResolvedValue()
    await wrapper.find('.storyline__edit-btn').trigger('click')
    const input = wrapper.find('.storyline__name-input')
    await input.setValue('Mon aventure')
    await input.trigger('keydown', { key: 'Enter' })
    expect(store.renameQuest).toHaveBeenCalledWith(1, 'Mon aventure')
    expect(wrapper.find('.storyline__name-input').exists()).toBe(false)
  })

  it('Escape key cancels without saving', async () => {
    vi.spyOn(store, 'renameQuest').mockResolvedValue()
    await wrapper.find('.storyline__edit-btn').trigger('click')
    await wrapper.find('.storyline__name-input').trigger('keydown', { key: 'Escape' })
    expect(store.renameQuest).not.toHaveBeenCalled()
    expect(wrapper.find('.storyline__name-input').exists()).toBe(false)
  })

  it('blank input commits null to clear the name', async () => {
    vi.spyOn(store, 'renameQuest').mockResolvedValue()
    await wrapper.find('.storyline__edit-btn').trigger('click')
    const input = wrapper.find('.storyline__name-input')
    await input.setValue('   ')
    await input.trigger('keydown', { key: 'Enter' })
    expect(store.renameQuest).toHaveBeenCalledWith(1, null)
  })
})
