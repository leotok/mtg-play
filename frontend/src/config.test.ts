import { describe, it, expect } from 'vitest'
import { config } from './config'

describe('config', () => {
  it('has apiUrl defined', () => {
    expect(config.apiUrl).toBeDefined()
    expect(typeof config.apiUrl).toBe('string')
  })

  it('has wsUrl defined', () => {
    expect(config.wsUrl).toBeDefined()
    expect(typeof config.wsUrl).toBe('string')
  })

  it('apiUrl contains protocol', () => {
    expect(config.apiUrl).toMatch(/^https?:\/\//)
  })

  it('wsUrl contains protocol or path', () => {
    expect(config.wsUrl).toMatch(/^https?:\/\//)
  })
})
