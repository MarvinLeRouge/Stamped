import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import MapView from '../MapView.vue'

vi.mock('@vue-leaflet/vue-leaflet', () => ({
  LMap: {
    name: 'LMap',
    template: '<div class="l-map"><slot /></div>',
    props: ['zoom', 'center'],
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
vi.mock('@/api', () => ({ default: { get: vi.fn() } }))

describe('MapView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders without error', () => {
    const wrapper = mount(MapView)
    expect(wrapper.exists()).toBe(true)
  })

  it('renders the map container', () => {
    const wrapper = mount(MapView)
    expect(wrapper.find('.l-map').exists()).toBe(true)
  })

  it('passes the correct zoom level', () => {
    const wrapper = mount(MapView)
    const map = wrapper.findComponent({ name: 'LMap' })
    expect(map.props('zoom')).toBe(5)
  })

  it('passes the correct center coordinates', () => {
    const wrapper = mount(MapView)
    const map = wrapper.findComponent({ name: 'LMap' })
    expect(map.props('center')).toEqual([46.8, 2.3])
  })

  it('passes the correct tile URL', () => {
    const wrapper = mount(MapView)
    const tile = wrapper.findComponent({ name: 'LTileLayer' })
    expect(tile.props('url')).toBe('/tiles/{z}/{x}/{y}.png')
  })
})
