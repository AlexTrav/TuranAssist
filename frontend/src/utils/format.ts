import type { AppLocale } from '../types'

const LOCALES: Record<AppLocale, string> = { ru: 'ru-RU', kk: 'kk-KZ', en: 'en-US' }

export function formatNumber(value: number, locale: AppLocale, digits = 1): string {
  return new Intl.NumberFormat(LOCALES[locale], { maximumFractionDigits: digits }).format(value)
}

// доля 0..1 -> «87%»
export function formatPercent(value: number, locale: AppLocale, digits = 0): string {
  return new Intl.NumberFormat(LOCALES[locale], { style: 'percent', maximumFractionDigits: digits }).format(value)
}

// доля с 95% доверительным интервалом: «0,755 [0,705; 0,799]»
export function formatProportion(p: { value: number; ci95: [number, number] }, locale: AppLocale): string {
  const f = (v: number) => new Intl.NumberFormat(LOCALES[locale], { minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(v)
  return `${f(p.value)} [${f(p.ci95[0])}; ${f(p.ci95[1])}]`
}

// длительность в секундах -> «2 ч 05 мин» / «3 мин 12 с» / «45 с» (единицы передаются уже переведёнными)
export function formatDuration(seconds: number, units: { h: string; m: string; s: string }): string {
  const s = Math.floor(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  if (h > 0) return `${h} ${units.h} ${String(m).padStart(2, '0')} ${units.m}`
  if (m > 0) return `${m} ${units.m} ${s % 60} ${units.s}`
  return `${s} ${units.s}`
}
