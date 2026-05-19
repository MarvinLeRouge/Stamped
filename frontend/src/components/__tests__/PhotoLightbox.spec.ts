import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import PhotoLightbox from '../PhotoLightbox.vue'
import { useLightboxStore } from '@/stores/lightbox'

describe('PhotoLightbox', () => {
  let wrapper: ReturnType<typeof mount>

  beforeEach(() => {
    setActivePinia(createPinia())
    wrapper = mount(PhotoLightbox, { attachTo: document.body })
  })

  afterEach(() => wrapper.unmount())

  it('renders nothing when no photo is open', () => {
    expect(document.querySelector('.lightbox')).toBeNull()
  })

  it('renders the lightbox when a photo is open', async () => {
    useLightboxStore().open(7)
    await flushPromises()
    expect(document.querySelector('.lightbox')).not.toBeNull()
  })

  it('shows the original image URL', async () => {
    useLightboxStore().open(7)
    await flushPromises()
    const img = document.querySelector<HTMLImageElement>('img.lightbox__img')
    expect(img?.src).toContain('/api/photos/7/original')
  })

  it('closes on backdrop click', async () => {
    const store = useLightboxStore()
    store.open(7)
    await flushPromises()
    document.querySelector<HTMLElement>('.lightbox')!.click()
    await flushPromises()
    expect(store.photoId).toBeNull()
  })

  it('closes on close button click', async () => {
    const store = useLightboxStore()
    store.open(7)
    await flushPromises()
    document.querySelector<HTMLElement>('.lightbox__close')!.click()
    await flushPromises()
    expect(store.photoId).toBeNull()
  })

  it('closes on Escape keydown', async () => {
    const store = useLightboxStore()
    store.open(7)
    await flushPromises()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(store.photoId).toBeNull()
  })

  it('does not close on other key presses', async () => {
    const store = useLightboxStore()
    store.open(7)
    await flushPromises()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }))
    await flushPromises()
    expect(store.photoId).toBe(7)
  })

  it('removes keydown listener on unmount', async () => {
    const store = useLightboxStore()
    store.open(7)
    await flushPromises()
    wrapper.unmount()
    store.open(7)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(store.photoId).toBe(7)
    wrapper = mount(PhotoLightbox, { attachTo: document.body })
  })
})
