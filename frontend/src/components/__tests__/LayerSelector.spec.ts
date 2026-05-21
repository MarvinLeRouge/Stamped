import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import LayerSelector from '../LayerSelector.vue'
import { useLayerStore } from '@/stores/layer'

describe('LayerSelector', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders a button for each layer', () => {
    const wrapper = mount(LayerSelector)
    expect(wrapper.findAll('.layer-selector__btn')).toHaveLength(3)
  })

  it('active button has the active class', () => {
    const wrapper = mount(LayerSelector)
    const activeBtn = wrapper.find('.layer-selector__btn--active')
    expect(activeBtn.text()).toBe('OSM')
  })

  it('clicking a button sets the active layer', async () => {
    const store = useLayerStore()
    const wrapper = mount(LayerSelector)
    await wrapper.findAll('.layer-selector__btn')[1]!.trigger('click')
    expect(store.activeLayerId).toBe('topo')
  })

  it('clicking satellite sets satellite layer', async () => {
    const store = useLayerStore()
    const wrapper = mount(LayerSelector)
    await wrapper.findAll('.layer-selector__btn')[2]!.trigger('click')
    expect(store.activeLayerId).toBe('satellite')
  })
})
