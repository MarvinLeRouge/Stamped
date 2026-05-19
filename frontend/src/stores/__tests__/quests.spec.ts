import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from '@/api'
import { useQuestsStore } from '@/stores/quests'

vi.mock('@/api', () => ({ default: { get: vi.fn(), patch: vi.fn() } }))
const mockApi = vi.mocked(api)

const mockQuests = [
  {
    id: 1,
    name: null,
    auto_name: 'Quest 2024-07-14',
    started_at: '2024-07-14T08:00:00Z',
    ended_at: '2024-07-14T12:00:00Z',
    photo_count: 3,
    has_gpx: false,
    bbox_lat_min: 45.0,
    bbox_lat_max: 46.0,
    bbox_lon_min: 6.0,
    bbox_lon_max: 7.0,
  },
]

describe('useQuestsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('initialises with empty quests and no selection', () => {
    const store = useQuestsStore()
    expect(store.quests).toEqual([])
    expect(store.selectedQuestId).toBeNull()
  })

  it('fetchQuests populates quests on success', async () => {
    mockApi.get.mockResolvedValue({ data: mockQuests })
    const store = useQuestsStore()
    await store.fetchQuests()
    expect(store.quests).toEqual(mockQuests)
    expect(store.error).toBeNull()
  })

  it('fetchQuests sets error on failure', async () => {
    mockApi.get.mockRejectedValue(new Error('network'))
    const store = useQuestsStore()
    await store.fetchQuests()
    expect(store.error).toBe('Failed to load quests')
  })

  it('selectQuest sets selectedQuestId', () => {
    const store = useQuestsStore()
    store.selectQuest(1)
    expect(store.selectedQuestId).toBe(1)
  })

  it('selectQuest with null clears selection', () => {
    const store = useQuestsStore()
    store.selectQuest(1)
    store.selectQuest(null)
    expect(store.selectedQuestId).toBeNull()
  })

  it('renameQuest updates the quest name in the list', async () => {
    const updated = { ...mockQuests[0], name: 'Mon aventure' }
    vi.mocked(api).patch.mockResolvedValue({ data: updated })
    const store = useQuestsStore()
    store.quests = [...mockQuests]
    await store.renameQuest(1, 'Mon aventure')
    expect(store.quests[0].name).toBe('Mon aventure')
  })

  it('renameQuest with null clears the name', async () => {
    const updated = { ...mockQuests[0], name: null }
    vi.mocked(api).patch.mockResolvedValue({ data: updated })
    const store = useQuestsStore()
    store.quests = [{ ...mockQuests[0], name: 'Old name' }]
    await store.renameQuest(1, null)
    expect(store.quests[0].name).toBeNull()
  })
})
