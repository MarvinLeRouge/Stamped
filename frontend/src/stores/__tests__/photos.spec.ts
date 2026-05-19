import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from '@/api'
import { usePhotosStore } from '@/stores/photos'

vi.mock('@/api', () => ({ default: { get: vi.fn() } }))
const mockApi = vi.mocked(api)

const mockPhotos = [
  {
    id: 1,
    lat: 45.0,
    lon: 6.0,
    captured_at: '2024-07-14T08:00:00Z',
    thumb_status: 'pending',
    quest_id: null,
    is_orphan: false,
  },
]

describe('usePhotosStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('initialises with empty photos', () => {
    const store = usePhotosStore()
    expect(store.photos).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchPhotos populates photos on success', async () => {
    mockApi.get.mockResolvedValue({ data: mockPhotos })
    const store = usePhotosStore()
    await store.fetchPhotos()
    expect(store.photos).toEqual(mockPhotos)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetchPhotos sets error on failure', async () => {
    mockApi.get.mockRejectedValue(new Error('network'))
    const store = usePhotosStore()
    await store.fetchPhotos()
    expect(store.error).toBe('Failed to load photos')
    expect(store.photos).toEqual([])
  })

  it('fetchPhotos passes filters as query params', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const store = usePhotosStore()
    await store.fetchPhotos({ lat_min: 44.0, lat_max: 46.0 })
    expect(mockApi.get).toHaveBeenCalledWith('/photos', {
      params: { lat_min: 44.0, lat_max: 46.0 },
    })
  })

  it('fetchPhotos strips undefined filters', async () => {
    mockApi.get.mockResolvedValue({ data: [] })
    const store = usePhotosStore()
    await store.fetchPhotos({ lat_min: 44.0, quest_id: undefined })
    const call = mockApi.get.mock.calls[0]?.[1] as { params: Record<string, unknown> } | undefined
    expect(call?.params).not.toHaveProperty('quest_id')
  })
})
