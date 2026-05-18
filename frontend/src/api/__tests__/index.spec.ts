import { describe, expect, it } from 'vitest'

import api from '@/api'

describe('api instance', () => {
  it('has correct baseURL', () => {
    expect(api.defaults.baseURL).toBe('/api')
  })

  it('has correct timeout', () => {
    expect(api.defaults.timeout).toBe(10_000)
  })
})
