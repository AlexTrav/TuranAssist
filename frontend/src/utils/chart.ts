export interface ChartPoint {
  x: number
  y: number
}

// масштабирует ряд значений в координаты SVG: x – равномерно по ширине, y – от 0 (низ) до max (верх)
export function scalePoints(values: number[], width: number, height: number, max?: number): ChartPoint[] {
  if (values.length === 0) return []
  const top = max ?? Math.max(...values, 1)
  const step = values.length > 1 ? width / (values.length - 1) : 0
  return values.map((v, i) => ({
    x: values.length > 1 ? i * step : width / 2,
    y: height - (Math.min(v, top) / top) * height,
  }))
}

// путь ломаной для <path d="...">
export function linePath(points: ChartPoint[]): string {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
}

// «красивый» верх оси: ближайшее сверху из 1, 2, 5 × 10^k
export function niceMax(value: number): number {
  if (value <= 0) return 1
  const power = 10 ** Math.floor(Math.log10(value))
  for (const k of [1, 2, 5, 10]) if (value <= k * power) return k * power
  return 10 * power
}
