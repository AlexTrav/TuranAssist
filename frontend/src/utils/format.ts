import type { AppLocale } from '../types'

const LOCALES: Record<AppLocale, string> = { ru: 'ru-RU', kk: 'kk-KZ', en: 'en-US' }

export function formatNumber(value: number, locale: AppLocale, digits = 1): string {
  return new Intl.NumberFormat(LOCALES[locale], { maximumFractionDigits: digits }).format(value)
}

// ровно digits знаков после запятой: «0,670», а не «0,67»
export function formatFixed(value: number, locale: AppLocale, digits: number): string {
  return new Intl.NumberFormat(LOCALES[locale], { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
}

// доля 0..1 -> «87%»
export function formatPercent(value: number, locale: AppLocale, digits = 0): string {
  return new Intl.NumberFormat(LOCALES[locale], { style: 'percent', maximumFractionDigits: digits }).format(value)
}

// доля с 95% доверительным интервалом: «0,755 [0,705; 0,799]»
export function formatProportion(p: { value: number; ci95: [number, number] }, locale: AppLocale): string {
  const f = (v: number) => formatFixed(v, locale, 3)
  return `${f(p.value)} [${f(p.ci95[0])}; ${f(p.ci95[1])}]`
}

// подслово SentencePiece для показа: служебный знак начала слова ▁ (его нет в шрифтах) -> «·»
export function formatPiece(piece: string): string {
  return piece.replace(/^▁/, '·')
}

// дата «2026-10-09» -> «9 октября 2026 г.» на языке интерфейса
export function formatDate(iso: string, locale: AppLocale): string {
  return new Intl.DateTimeFormat(LOCALES[locale], { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date(`${iso}T12:00:00`))
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
