import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import AllPhotosPanel from '../AllPhotosPanel.vue'
import { useQuestsStore } from '@/stores/quests'
import api from '@/api'

vi.mock('@/api', () => ({ default: { get: vi.fn() } }))

const PHOTOS = [
  {
    id: 1,
    captured_at: '2024-01-01T08:00:00Z',
    thumb_status: 'done',
    is_orphan: false,
    quest_id: 1,
  },
  { id: 2, captured_at: null, thumb_status: 'pending', is_orphan: true, quest_id: null },
]

describe('AllPhotosPanel', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(api.get).mockResolvedValue({ data: PHOTOS })
    wrapper = mount(AllPhotosPanel, { attachTo: document.body })
  })

  afterEach(() => wrapper.unmount())

  it('renders nothing when showAllPhotos is false', () => {
    expect(wrapper.find('.all-photos').exists()).toBe(false)
  })

  it('renders panel when showAllPhotos is true', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.find('.all-photos').exists()).toBe(true)
  })

  it('renders one item per photo', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.findAll('.all-photos__item')).toHaveLength(2)
  })

  it('shows orphan tag for orphan photos', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.find('.all-photos__tag--orphan').exists()).toBe(true)
  })

  it('shows sans-quest tag for photos without quest', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.find('.all-photos__tag--noquest').exists()).toBe(true)
  })

  it('filter "placed" adds orphan=false param', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    await wrapper.find('.all-photos__filter:nth-child(2)').trigger('click')
    await flushPromises()
    expect(vi.mocked(api.get).mock.calls.at(-1)?.[0]).toContain('orphan=false')
  })

  it('filter "orphan" adds orphan=true param', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    await wrapper.find('.all-photos__filter:nth-child(3)').trigger('click')
    await flushPromises()
    expect(vi.mocked(api.get).mock.calls.at(-1)?.[0]).toContain('orphan=true')
  })

  it('filter "all" removes orphan param', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    await wrapper.find('.all-photos__filter:nth-child(3)').trigger('click')
    await flushPromises()
    await wrapper.find('.all-photos__filter:nth-child(1)').trigger('click')
    await flushPromises()
    const lastCall = vi.mocked(api.get).mock.calls.at(-1)?.[0] as string
    expect(lastCall).not.toContain('orphan=')
  })

  it('renders pending placeholder for non-done photos', async () => {
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.find('.all-photos__thumb--pending').exists()).toBe(true)
  })

  it('shows empty message when no photos', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    useQuestsStore().showAllPhotos = true
    await flushPromises()
    expect(wrapper.text()).toContain('No photos')
  })
})
