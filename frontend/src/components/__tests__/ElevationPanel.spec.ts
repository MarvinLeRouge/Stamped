import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import ElevationPanel from '../ElevationPanel.vue'
import { useElevationStore } from '@/stores/elevation'
import { useHighlightStore } from '@/stores/highlight'
import { useQuestsStore } from '@/stores/quests'
import api from '@/api'

vi.mock('@/api', () => ({ default: { get: vi.fn() } }))

const POINTS = [
  { d: 0, alt: 100, t: '2024-06-01T08:00:00Z' },
  { d: 500, alt: 150, t: '2024-06-01T08:10:00Z' },
  { d: 1000, alt: 200, t: '2024-06-01T08:20:00Z' },
]

describe('ElevationPanel', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    vi.mocked(api.get).mockResolvedValue({ data: POINTS })
    wrapper = mount(ElevationPanel, { attachTo: document.body })
  })

  afterEach(() => wrapper.unmount())

  it('renders nothing when not visible', () => {
    expect(wrapper.find('.elevation-panel').exists()).toBe(false)
  })

  it('renders nothing when visible but no points', () => {
    useElevationStore().visible = true
    expect(wrapper.find('.elevation-panel').exists()).toBe(false)
  })

  it('renders panel when visible and has points', async () => {
    const store = useElevationStore()
    store.setPoints(POINTS)
    store.visible = true
    await flushPromises()
    expect(wrapper.find('.elevation-panel').exists()).toBe(true)
  })

  it('renders SVG polyline with points', async () => {
    const store = useElevationStore()
    store.setPoints(POINTS)
    store.visible = true
    await flushPromises()
    expect(wrapper.find('polyline').exists()).toBe(true)
  })

  it('fetches elevation when quest with GPX is selected', async () => {
    const questsStore = useQuestsStore()
    questsStore.quests = [
      {
        id: 1,
        name: null,
        auto_name: 'Q',
        started_at: null,
        ended_at: null,
        photo_count: 0,
        has_gpx: true,
        bbox_lat_min: null,
        bbox_lat_max: null,
        bbox_lon_min: null,
        bbox_lon_max: null,
      },
    ]
    questsStore.selectedQuestId = 1
    await flushPromises()
    expect(api.get).toHaveBeenCalledWith('/quests/1/elevation')
  })

  it('does not fetch elevation when quest has no GPX', async () => {
    const questsStore = useQuestsStore()
    questsStore.quests = [
      {
        id: 2,
        name: null,
        auto_name: 'Q',
        started_at: null,
        ended_at: null,
        photo_count: 0,
        has_gpx: false,
        bbox_lat_min: null,
        bbox_lat_max: null,
        bbox_lon_min: null,
        bbox_lon_max: null,
      },
    ]
    questsStore.selectedQuestId = 2
    await flushPromises()
    expect(api.get).not.toHaveBeenCalled()
  })

  it('mouseleave clears highlight timestamp', async () => {
    const store = useElevationStore()
    const highlightStore = useHighlightStore()
    store.setPoints(POINTS)
    store.visible = true
    await flushPromises()
    highlightStore.highlight(null, '2024-06-01T08:00:00Z')
    await wrapper.find('svg').trigger('mouseleave')
    expect(highlightStore.hoveredTimestamp).toBeNull()
  })

  it('hoveredTimestamp matching a point sets highlightedX', async () => {
    const store = useElevationStore()
    const highlightStore = useHighlightStore()
    store.setPoints(POINTS)
    store.visible = true
    await flushPromises()
    // Set timestamp matching the second point (d=500) — triggers highlightedX computed
    highlightStore.highlight(null, '2024-06-01T08:10:00Z')
    await flushPromises()
    // The storyline cursor line should be rendered
    expect(wrapper.find('.elev-cursor').exists()).toBe(true)
  })

  it('mousemove sets hoverX and syncs highlight timestamp', async () => {
    const store = useElevationStore()
    const highlightStore = useHighlightStore()
    store.setPoints(POINTS)
    store.visible = true
    await flushPromises()

    const svg = wrapper.find('svg').element as SVGSVGElement
    svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: 800, height: 140 }) as DOMRect

    await wrapper.find('svg').trigger('mousemove', { clientX: 400, clientY: 70 })
    await flushPromises()

    expect(highlightStore.hoveredTimestamp).not.toBeNull()
  })
})
