import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import MapView from '../MapView.vue'
import { usePhotosStore } from '@/stores/photos'
import { useQuestsStore } from '@/stores/quests'
import { usePlacementStore } from '@/stores/placement'
import { useHighlightStore } from '@/stores/highlight'
import api from '@/api'

// ── Leaflet mocks ─────────────────────────────────────────────────────────────

const mockMarkerEl = { classList: { add: vi.fn(), remove: vi.fn() } }
const mockMarker = {
  bindPopup: vi.fn().mockReturnThis(),
  on: vi.fn(),
  getElement: vi.fn(() => mockMarkerEl),
}
const mockCluster = { addLayer: vi.fn() }
const mockContainer = { style: { cursor: '' } }
const mockMap = {
  removeLayer: vi.fn(),
  addLayer: vi.fn(),
  on: vi.fn(),
  fitBounds: vi.fn(),
  getContainer: vi.fn(() => mockContainer),
  getBounds: vi.fn().mockReturnValue({
    getSouth: () => 44.0,
    getNorth: () => 46.0,
    getWest: () => 5.0,
    getEast: () => 7.0,
  }),
}

const mockPolyline = { addTo: vi.fn() }

vi.mock('leaflet', () => ({
  default: {
    marker: vi.fn(() => mockMarker),
    markerClusterGroup: vi.fn(() => mockCluster),
    polyline: vi.fn(() => mockPolyline),
  },
}))

vi.mock('@vue-leaflet/vue-leaflet', () => ({
  LMap: {
    name: 'LMap',
    template: '<div class="l-map"><slot /></div>',
    props: ['zoom', 'center'],
    setup: () => ({ leafletObject: mockMap }),
  },
  LTileLayer: {
    name: 'LTileLayer',
    template: '<div class="l-tile-layer" />',
    props: ['url', 'attribution', 'layerType'],
  },
}))

vi.mock('leaflet.markercluster', () => ({}))
vi.mock('leaflet.markercluster/dist/MarkerCluster.css', () => ({}))
vi.mock('leaflet.markercluster/dist/MarkerCluster.Default.css', () => ({}))
vi.mock('@/api', () => ({ default: { get: vi.fn(), patch: vi.fn() } }))

// ── Rendering tests ───────────────────────────────────────────────────────────

describe('MapView — rendering', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders without error', () => {
    expect(mount(MapView).exists()).toBe(true)
  })

  it('renders the map container', () => {
    expect(mount(MapView).find('.l-map').exists()).toBe(true)
  })

  it('passes the correct zoom level', () => {
    const map = mount(MapView).findComponent({ name: 'LMap' })
    expect(map.props('zoom')).toBe(5)
  })

  it('passes the correct center coordinates', () => {
    const map = mount(MapView).findComponent({ name: 'LMap' })
    expect(map.props('center')).toEqual([46.8, 2.3])
  })

  it('passes the correct tile URL', () => {
    const tile = mount(MapView).findComponent({ name: 'LTileLayer' })
    expect(tile.props('url')).toBe('/tiles/{z}/{x}/{y}.png')
  })
})

// ── Logic tests ───────────────────────────────────────────────────────────────

describe('MapView — logic', () => {
  let photosStore: ReturnType<typeof usePhotosStore>
  let questsStore: ReturnType<typeof useQuestsStore>
  let wrapper: ReturnType<typeof mount>

  beforeEach(async () => {
    vi.clearAllMocks()
    setActivePinia(createPinia())
    photosStore = usePhotosStore()
    questsStore = useQuestsStore()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    vi.spyOn(questsStore, 'fetchQuests').mockResolvedValue()

    wrapper = mount(MapView)
    wrapper.findComponent({ name: 'LMap' }).vm.$emit('ready')
    await flushPromises()
  })

  afterEach(() => wrapper.unmount())

  it('fetches photos and quests on map ready', () => {
    expect(photosStore.fetchPhotos).toHaveBeenCalledTimes(1)
    expect(questsStore.fetchQuests).toHaveBeenCalledTimes(1)
  })

  it('registers moveend listener', () => {
    expect(mockMap.on).toHaveBeenCalledWith('moveend', expect.any(Function))
  })

  async function emitReadyWithPhotos(photos: typeof photosStore.photos): Promise<void> {
    vi.clearAllMocks()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    vi.spyOn(questsStore, 'fetchQuests').mockResolvedValue()
    photosStore.photos = photos
    wrapper.findComponent({ name: 'LMap' }).vm.$emit('ready')
    await flushPromises()
  }

  it('adds markers for photos with GPS', async () => {
    await emitReadyWithPhotos([
      {
        id: 1,
        lat: 45.0,
        lon: 6.0,
        captured_at: '2024-07-14T08:00:00Z',
        thumb_status: 'done',
        quest_id: null,
        is_orphan: false,
      },
    ])
    expect(mockCluster.addLayer).toHaveBeenCalled()
    expect(mockMap.addLayer).toHaveBeenCalledWith(mockCluster)
  })

  it('skips photos without GPS', async () => {
    await emitReadyWithPhotos([
      {
        id: 2,
        lat: null,
        lon: null,
        captured_at: null,
        thumb_status: 'pending',
        quest_id: null,
        is_orphan: true,
      },
    ])
    expect(mockMarker.bindPopup).not.toHaveBeenCalled()
  })

  it('buildPopup with done status contains img', async () => {
    await emitReadyWithPhotos([
      {
        id: 3,
        lat: 45.0,
        lon: 6.0,
        captured_at: '2024-07-14T08:00:00Z',
        thumb_status: 'done',
        quest_id: null,
        is_orphan: false,
      },
    ])
    const popup = mockMarker.bindPopup.mock.calls.at(-1)?.[0] as string
    expect(popup).toContain('<img')
    expect(popup).toContain('/api/photos/3/thumb')
    expect(popup).toContain('2024')
  })

  it('buildPopup with pending status shows Generating', async () => {
    await emitReadyWithPhotos([
      {
        id: 4,
        lat: 45.0,
        lon: 6.0,
        captured_at: null,
        thumb_status: 'pending',
        quest_id: null,
        is_orphan: false,
      },
    ])
    const popup = mockMarker.bindPopup.mock.calls.at(-1)?.[0] as string
    expect(popup).toContain('Generating')
    expect(popup).not.toContain('<img')
  })

  it('loadVisiblePhotos fetches with bbox filters', async () => {
    const moveendHandler = mockMap.on.mock.calls.find(
      (c) => c[0] === 'moveend',
    )?.[1] as () => Promise<void>
    vi.clearAllMocks()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    await moveendHandler()
    expect(photosStore.fetchPhotos).toHaveBeenCalledWith(
      expect.objectContaining({ lat_min: 44.0, lat_max: 46.0 }),
    )
  })

  it('loadVisiblePhotos includes quest_id when selected', async () => {
    questsStore.selectedQuestId = 1
    const moveendHandler = mockMap.on.mock.calls.find(
      (c) => c[0] === 'moveend',
    )?.[1] as () => Promise<void>
    vi.clearAllMocks()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    await moveendHandler()
    expect(photosStore.fetchPhotos).toHaveBeenCalledWith(expect.objectContaining({ quest_id: 1 }))
  })

  it('watch without quest bbox falls back to loadVisiblePhotos', async () => {
    vi.clearAllMocks()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    questsStore.selectedQuestId = 99 // quest not in store → no bbox
    await flushPromises()
    expect(photosStore.fetchPhotos).toHaveBeenCalled()
  })

  it('watch with quest bbox calls fitBounds', async () => {
    questsStore.quests = [
      {
        id: 5,
        name: null,
        auto_name: 'Quest',
        started_at: null,
        ended_at: null,
        photo_count: 3,
        has_gpx: false,
        bbox_lat_min: 44.0,
        bbox_lat_max: 46.0,
        bbox_lon_min: 5.0,
        bbox_lon_max: 7.0,
      },
    ]
    questsStore.selectedQuestId = 5
    await flushPromises()
    expect(mockMap.fitBounds).toHaveBeenCalledWith(
      [
        [44.0, 5.0],
        [46.0, 7.0],
      ],
      { padding: [40, 40] },
    )
  })

  it('selecting a quest with two GPX segments adds two polylines', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        [
          [44.0, 6.0],
          [44.1, 6.1],
        ],
        [
          [45.0, 7.0],
          [45.1, 7.1],
        ],
      ],
    } as never)
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    vi.clearAllMocks()
    questsStore.selectedQuestId = 10
    await flushPromises()
    const polyCalls = mockMap.addLayer.mock.calls.filter((c) => c[0] === mockPolyline)
    expect(polyCalls).toHaveLength(2)
  })

  it('deselecting a quest removes all polylines', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        [
          [44.0, 6.0],
          [44.1, 6.1],
        ],
        [
          [45.0, 7.0],
          [45.1, 7.1],
        ],
      ],
    } as never)
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    questsStore.selectedQuestId = 10
    await flushPromises()

    vi.clearAllMocks()
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    questsStore.selectedQuestId = null
    await flushPromises()
    const removeCalls = mockMap.removeLayer.mock.calls.filter((c) => c[0] === mockPolyline)
    expect(removeCalls).toHaveLength(2)
  })

  it('map click in placement mode patches photo and cancels placement', async () => {
    vi.mocked(api.patch).mockResolvedValue({} as never)
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    const placementStore = usePlacementStore()
    placementStore.startPlacing(42)

    const clickHandler = mockMap.on.mock.calls.find((c) => c[0] === 'click')?.[1] as (
      e: unknown,
    ) => Promise<void>
    await clickHandler({ latlng: { lat: 44.0, lng: 6.0 } })
    await flushPromises()

    expect(api.patch).toHaveBeenCalledWith('/photos/42', { lat: 44.0, lon: 6.0 })
    expect(placementStore.placingPhotoId).toBeNull()
  })

  it('map click outside placement mode does nothing', async () => {
    vi.mocked(api.patch).mockResolvedValue({} as never)
    const clickHandler = mockMap.on.mock.calls.find((c) => c[0] === 'click')?.[1] as (
      e: unknown,
    ) => Promise<void>
    await clickHandler({ latlng: { lat: 44.0, lng: 6.0 } })
    expect(api.patch).not.toHaveBeenCalled()
  })

  it('placing a photo sets crosshair cursor on map container', async () => {
    const placementStore = usePlacementStore()
    mockContainer.style.cursor = ''
    placementStore.startPlacing(5)
    await flushPromises()
    expect(mockContainer.style.cursor).toBe('crosshair')
  })

  it('cancelling placement restores default cursor', async () => {
    const placementStore = usePlacementStore()
    placementStore.startPlacing(5)
    await flushPromises()
    placementStore.cancel()
    await flushPromises()
    expect(mockContainer.style.cursor).toBe('')
  })

  it('highlighting a photo adds CSS class to its marker element', async () => {
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    photosStore.photos = [
      {
        id: 7,
        lat: 44.0,
        lon: 6.0,
        captured_at: null,
        thumb_status: 'done',
        quest_id: null,
        is_orphan: false,
      },
    ]
    wrapper.findComponent({ name: 'LMap' }).vm.$emit('ready')
    await flushPromises()
    const highlightStore = useHighlightStore()
    highlightStore.highlight(7)
    await flushPromises()
    expect(mockMarkerEl.classList.add).toHaveBeenCalledWith('marker--highlighted')
  })

  it('un-highlighting removes CSS class from previous marker', async () => {
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    photosStore.photos = [
      {
        id: 7,
        lat: 44.0,
        lon: 6.0,
        captured_at: null,
        thumb_status: 'done',
        quest_id: null,
        is_orphan: false,
      },
    ]
    wrapper.findComponent({ name: 'LMap' }).vm.$emit('ready')
    await flushPromises()
    const highlightStore = useHighlightStore()
    highlightStore.highlight(7)
    await flushPromises()
    mockMarkerEl.classList.remove.mockClear()
    highlightStore.highlight(null)
    await flushPromises()
    expect(mockMarkerEl.classList.remove).toHaveBeenCalledWith('marker--highlighted')
  })

  it('segments with fewer than two points are skipped', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: [
        [[44.0, 6.0]],
        [
          [45.0, 7.0],
          [45.1, 7.1],
        ],
      ],
    } as never)
    vi.spyOn(photosStore, 'fetchPhotos').mockResolvedValue()
    vi.clearAllMocks()
    questsStore.selectedQuestId = 11
    await flushPromises()
    const polyCalls = mockMap.addLayer.mock.calls.filter((c) => c[0] === mockPolyline)
    expect(polyCalls).toHaveLength(1)
  })
})
