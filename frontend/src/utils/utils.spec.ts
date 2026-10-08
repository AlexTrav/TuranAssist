import { describe, expect, it } from 'vitest'
import { linePath, niceMax, scalePoints } from './chart'
import { formatDuration, formatPercent, formatProportion } from './format'

describe('format', () => {
  it('formats percent and proportion with confidence interval per locale', () => {
    expect(formatPercent(0.876, 'en')).toBe('88%')
    expect(formatProportion({ value: 0.755, ci95: [0.705, 0.799] }, 'en')).toBe('0.755 [0.705; 0.799]')
    expect(formatProportion({ value: 0.755, ci95: [0.705, 0.799] }, 'ru')).toBe('0,755 [0,705; 0,799]')
  })

  it('formats durations', () => {
    const units = { h: 'h', m: 'min', s: 's' }
    expect(formatDuration(45, units)).toBe('45 s')
    expect(formatDuration(192, units)).toBe('3 min 12 s')
    expect(formatDuration(7500, units)).toBe('2 h 05 min')
  })
})

describe('chart', () => {
  it('scales values bottom-up and builds a path', () => {
    const pts = scalePoints([0, 5, 10], 100, 50, 10)
    expect(pts).toEqual([
      { x: 0, y: 50 },
      { x: 50, y: 25 },
      { x: 100, y: 0 },
    ])
    expect(linePath(pts)).toBe('M0.0,50.0 L50.0,25.0 L100.0,0.0')
  })

  it('clips values above max and centers a single point', () => {
    expect(scalePoints([20], 100, 50, 10)).toEqual([{ x: 50, y: 0 }])
  })

  it('picks a nice axis maximum', () => {
    expect(niceMax(7.3)).toBe(10)
    expect(niceMax(13)).toBe(20)
    expect(niceMax(42)).toBe(50)
    expect(niceMax(0)).toBe(1)
  })
})
