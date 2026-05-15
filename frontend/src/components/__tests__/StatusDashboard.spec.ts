import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import StatusDashboard from '../StatusDashboard.vue'
import { useStatusStore } from '@/stores/status'

vi.mock('@/api', () => ({
  default: { get: vi.fn<() => Promise<unknown>>() },
}))

describe('StatusDashboard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('shows loading state initially', () => {
    const store = useStatusStore()
    store.loading = true
    const wrapper = mount(StatusDashboard)
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows error when server is unreachable', () => {
    const store = useStatusStore()
    store.error = 'Server unreachable'
    const wrapper = mount(StatusDashboard)
    expect(wrapper.text()).toContain('Server unreachable')
  })

  it('displays photo and quest counts from status', () => {
    const store = useStatusStore()
    store.status = {
      photos_total: 42,
      thumbs_done: 40,
      thumbs_pending: 2,
      orphans: 0,
      gpx_files: 3,
      quests: 7,
      last_index_at: null,
    }
    const wrapper = mount(StatusDashboard)
    expect(wrapper.text()).toContain('42 photos')
    expect(wrapper.text()).toContain('7 quests')
  })

  it('shows orphan count only when non-zero', () => {
    const store = useStatusStore()
    store.status = {
      photos_total: 10,
      thumbs_done: 10,
      thumbs_pending: 0,
      orphans: 3,
      gpx_files: 0,
      quests: 1,
      last_index_at: null,
    }
    const wrapper = mount(StatusDashboard)
    expect(wrapper.text()).toContain('3 orphans')
  })

  it('hides orphan count when zero', () => {
    const store = useStatusStore()
    store.status = {
      photos_total: 10,
      thumbs_done: 10,
      thumbs_pending: 0,
      orphans: 0,
      gpx_files: 0,
      quests: 1,
      last_index_at: null,
    }
    const wrapper = mount(StatusDashboard)
    expect(wrapper.text()).not.toContain('orphan')
  })
})
