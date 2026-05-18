import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import api from '@/api'
import { useStatusStore } from '@/stores/status'

vi.mock('@/api', () => ({
  default: { get: vi.fn() },
}))

const mockApi = vi.mocked(api)

const mockStatus = {
  photos_total: 10,
  thumbs_done: 8,
  thumbs_pending: 2,
  orphans: 1,
  gpx_files: 2,
  quests: 3,
  last_index_at: '2024-07-14T08:00:00Z',
}

describe('useStatusStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.resetAllMocks()
  })

  it('initialises with null status', () => {
    const store = useStatusStore()
    expect(store.status).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('fetch sets loading to true then false', async () => {
    mockApi.get.mockResolvedValue({ data: mockStatus })
    const store = useStatusStore()
    const promise = store.fetch()
    expect(store.loading).toBe(true)
    await promise
    expect(store.loading).toBe(false)
  })

  it('fetch updates status on success', async () => {
    mockApi.get.mockResolvedValue({ data: mockStatus })
    const store = useStatusStore()
    await store.fetch()
    expect(store.status).toEqual(mockStatus)
    expect(store.error).toBeNull()
  })

  it('fetch sets error on failure', async () => {
    mockApi.get.mockRejectedValue(new Error('Network error'))
    const store = useStatusStore()
    await store.fetch()
    expect(store.error).toBe('Server unreachable')
    expect(store.status).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('fetch clears previous error on new call', async () => {
    mockApi.get.mockRejectedValueOnce(new Error('fail'))
    const store = useStatusStore()
    await store.fetch()
    expect(store.error).toBe('Server unreachable')

    mockApi.get.mockResolvedValue({ data: mockStatus })
    await store.fetch()
    expect(store.error).toBeNull()
  })
})
