import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import QuestList from '../QuestList.vue'
import { useQuestsStore } from '@/stores/quests'

vi.mock('@/api', () => ({ default: { get: vi.fn().mockResolvedValue({ data: [] }) } }))

describe('QuestList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('shows loading state', () => {
    const store = useQuestsStore()
    store.loading = true
    const wrapper = mount(QuestList)
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows empty message when no quests', () => {
    const wrapper = mount(QuestList)
    expect(wrapper.text()).toContain('No quests yet')
  })

  it('renders quest list', () => {
    const store = useQuestsStore()
    store.quests = [
      {
        id: 1,
        name: 'Mont Blanc',
        auto_name: 'Quest 2024-07-14',
        started_at: '2024-07-14T08:00:00Z',
        ended_at: '2024-07-14T12:00:00Z',
        photo_count: 5,
        has_gpx: true,
        bbox_lat_min: null,
        bbox_lat_max: null,
        bbox_lon_min: null,
        bbox_lon_max: null,
      },
    ]
    const wrapper = mount(QuestList)
    expect(wrapper.text()).toContain('Mont Blanc')
    expect(wrapper.text()).toContain('5 photos')
    expect(wrapper.text()).toContain('GPX')
  })

  it('uses auto_name when name is null', () => {
    const store = useQuestsStore()
    store.quests = [
      {
        id: 1,
        name: null,
        auto_name: 'Quest 2024-07-14',
        started_at: null,
        ended_at: null,
        photo_count: 2,
        has_gpx: false,
        bbox_lat_min: null,
        bbox_lat_max: null,
        bbox_lon_min: null,
        bbox_lon_max: null,
      },
    ]
    const wrapper = mount(QuestList)
    expect(wrapper.text()).toContain('Quest 2024-07-14')
  })

  it('click toggles quest selection', async () => {
    const store = useQuestsStore()
    vi.spyOn(store, 'fetchQuests').mockResolvedValue()
    store.quests = [
      {
        id: 1,
        name: null,
        auto_name: 'Quest 2024-07-14',
        started_at: null,
        ended_at: null,
        photo_count: 1,
        has_gpx: false,
        bbox_lat_min: null,
        bbox_lat_max: null,
        bbox_lon_min: null,
        bbox_lon_max: null,
      },
    ]
    const wrapper = mount(QuestList)
    await wrapper.find('li').trigger('click')
    expect(store.selectedQuestId).toBe(1)
    await wrapper.find('li').trigger('click')
    expect(store.selectedQuestId).toBeNull()
  })
})
