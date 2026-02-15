import { describe, it, expect } from 'vitest'
import { getColorGroupName, COLOR_MAP, COLOR_GROUPS } from './colors'

describe('colors', () => {
  describe('COLOR_MAP', () => {
    it('contains all five magic colors', () => {
      expect(COLOR_MAP).toHaveProperty('W')
      expect(COLOR_MAP).toHaveProperty('U')
      expect(COLOR_MAP).toHaveProperty('B')
      expect(COLOR_MAP).toHaveProperty('R')
      expect(COLOR_MAP).toHaveProperty('G')
    })

    it('has correct color names', () => {
      expect(COLOR_MAP.W.name).toBe('White')
      expect(COLOR_MAP.U.name).toBe('Blue')
      expect(COLOR_MAP.B.name).toBe('Black')
      expect(COLOR_MAP.R.name).toBe('Red')
      expect(COLOR_MAP.G.name).toBe('Green')
    })
  })

  describe('COLOR_GROUPS', () => {
    it('contains mono color groups', () => {
      expect(COLOR_GROUPS.W).toBe('Mono White')
      expect(COLOR_GROUPS.U).toBe('Mono Blue')
      expect(COLOR_GROUPS.B).toBe('Mono Black')
      expect(COLOR_GROUPS.R).toBe('Mono Red')
      expect(COLOR_GROUPS.G).toBe('Mono Green')
    })

    it('contains two-color guild groups', () => {
      expect(COLOR_GROUPS.WU).toBe('Azorius')
      expect(COLOR_GROUPS.UB).toBe('Dimir')
      expect(COLOR_GROUPS.BR).toBe('Rakdos')
      expect(COLOR_GROUPS.RG).toBe('Gruul')
      expect(COLOR_GROUPS.GW).toBe('Selesnya')
    })

    it('contains five color group', () => {
      expect(COLOR_GROUPS.WUBRG).toBe('Five Color')
    })
  })

  describe('getColorGroupName', () => {
    it('returns Colorless for empty array', () => {
      expect(getColorGroupName([])).toBe('Colorless')
    })

    it('returns Colorless for null/undefined', () => {
      expect(getColorGroupName(null as any)).toBe('Colorless')
      expect(getColorGroupName(undefined as any)).toBe('Colorless')
    })

    it('returns mono color names for single colors', () => {
      expect(getColorGroupName(['W'])).toBe('Mono White')
      expect(getColorGroupName(['U'])).toBe('Mono Blue')
      expect(getColorGroupName(['B'])).toBe('Mono Black')
      expect(getColorGroupName(['R'])).toBe('Mono Red')
      expect(getColorGroupName(['G'])).toBe('Mono Green')
    })

    it('returns guild names for two-color combinations', () => {
      expect(getColorGroupName(['W', 'U'])).toBe('Azorius')
      expect(getColorGroupName(['U', 'B'])).toBe('Dimir')
    })

    it('handles color order independently', () => {
      expect(getColorGroupName(['U', 'W'])).toBe('Azorius')
      expect(getColorGroupName(['W', 'U'])).toBe('Azorius')
    })

    it('filters out invalid colors', () => {
      expect(getColorGroupName(['W', 'X', 'U'])).toBe('Azorius')
    })

    it('handles color order independently', () => {
      expect(getColorGroupName(['U', 'W'])).toBe('Azorius')
      expect(getColorGroupName(['W', 'U'])).toBe('Azorius')
    })

    it('filters out invalid colors', () => {
      expect(getColorGroupName(['W', 'X', 'U'])).toBe('Azorius')
    })

    it('returns mono color for known color with unknown', () => {
      expect(getColorGroupName(['W', 'X'])).toBe('Mono White')
    })

    it('returns shard names for three-color combinations', () => {
      expect(getColorGroupName(['W', 'B', 'R'])).toBe('Mardu')
      expect(getColorGroupName(['U', 'B', 'R'])).toBe('Grixis')
      expect(getColorGroupName(['W', 'U', 'B'])).toBe('Esper')
      expect(getColorGroupName(['W', 'B', 'G'])).toBe('Abzan')
    })

    it('handles three-color order independently', () => {
      expect(getColorGroupName(['R', 'W', 'B'])).toBe('Mardu')
      expect(getColorGroupName(['R', 'B', 'U'])).toBe('Grixis')
    })

    it('returns Five Color for all five colors', () => {
      expect(getColorGroupName(['W', 'U', 'B', 'R', 'G'])).toBe('Five Color')
    })

    it('handles five-color order independently', () => {
      expect(getColorGroupName(['R', 'G', 'W', 'U', 'B'])).toBe('Five Color')
    })

    it('handles whitespace in colors', () => {
      expect(getColorGroupName([' W '])).toBe('Mono White')
      expect(getColorGroupName(['W', ' U '])).toBe('Azorius')
    })

    it('handles empty strings', () => {
      expect(getColorGroupName([''])).toBe('Colorless')
      expect(getColorGroupName(['W', ''])).toBe('Mono White')
    })

    it('handles duplicates', () => {
      expect(getColorGroupName(['W', 'W'])).toBe('Mono White')
      expect(getColorGroupName(['W', 'W', 'U'])).toBe('Azorius')
    })
  })
})
