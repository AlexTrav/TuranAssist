import { describe, expect, it } from 'vitest'
import type { TuitionCatalog } from '../types'
import { areaPath, bucketLabel } from './chart'
import { parseInline, parseRichText } from './richText'
import { levelsOf, optionsOf, priceOf, totalOf } from './tuition'

describe('richText', () => {
  it('splits paragraphs and bullet lists', () => {
    const blocks = parseRichText('Стоимость:\n- очная – 1 476 600;\n- заочная – 738 300.\n\nСкидки – в разделе.')
    expect(blocks.map((b) => b.type)).toEqual(['p', 'list', 'p'])
    expect(blocks[1].type === 'list' && blocks[1].items).toHaveLength(2)
  })

  it('turns urls, phones and emails into links and keeps trailing punctuation as text', () => {
    const parts = parseInline('Сайт https://turan.edu.kz/ru/x. Тел.: +7 (727) 260 40 00, почта info@turan.edu.kz')
    expect(parts.filter((p) => p.type === 'link')).toEqual([
      { type: 'link', href: 'https://turan.edu.kz/ru/x', label: 'turan.edu.kz/ru/x' },
      { type: 'link', href: 'tel:+77272604000', label: '+7 (727) 260 40 00' },
      { type: 'link', href: 'mailto:info@turan.edu.kz', label: 'info@turan.edu.kz' },
    ])
    expect(parts[2]).toEqual({ type: 'text', value: '.' })
  })

  it('never produces html – text stays text', () => {
    const parts = parseInline('<img src=x onerror=alert(1)>')
    expect(parts).toEqual([{ type: 'text', value: '<img src=x onerror=alert(1)>' }])
  })
})

const catalog: TuitionCatalog = {
  plans: [
    { id: 'bachelor_4y', level: 'bachelor', label: { ru: 'очная, 4 года', kk: '', en: '' } },
    { id: 'bachelor_distance_university', level: 'bachelor', label: { ru: 'после вуза', kk: '', en: '' } },
    { id: 'master_research_2y', level: 'postgrad', label: { ru: 'магистратура, 2 года', kk: '', en: '' } },
  ],
  programs: [
    {
      id: 'ir',
      name: { ru: 'Международные отношения', kk: '', en: '' },
      prices: [
        { plan: 'bachelor_4y', main: 1476600, english: 1814700 },
        { plan: 'bachelor_distance_university', main: 669300 },
        { plan: 'master_research_2y', main: 1483500 },
      ],
    },
    { id: 'clinical', name: { ru: 'Клиническая психология', kk: '', en: '' }, prices: [{ plan: 'master_research_2y', main: 1483500 }] },
  ],
}

describe('tuition calculator', () => {
  it('lists only levels and plans that have prices', () => {
    expect(levelsOf(catalog.programs[0], catalog)).toEqual(['bachelor', 'postgrad'])
    expect(levelsOf(catalog.programs[1], catalog)).toEqual(['postgrad'])
    expect(optionsOf(catalog.programs[0], 'bachelor', catalog).map((o) => o.plan.id)).toEqual(['bachelor_4y', 'bachelor_distance_university'])
  })

  it('computes price per year and for the whole program', () => {
    const [full, distance] = optionsOf(catalog.programs[0], 'bachelor', catalog)
    expect(priceOf(full, true)).toBe(1814700)
    expect(priceOf(distance, true)).toBe(669300) // английского отделения нет – основная цена
    expect(totalOf(full, false)).toBe(4 * 1476600)
    expect(totalOf(distance, false)).toBeNull() // срок на сайте не указан
  })
})

describe('chart helpers', () => {
  it('closes the area under the line', () => {
    expect(areaPath([{ x: 0, y: 10 }, { x: 50, y: 5 }], 20)).toBe('M0.0,10.0 L50.0,5.0 L50.0,20 L0.0,20 Z')
    expect(areaPath([], 20)).toBe('')
  })

  it('labels histogram buckets', () => {
    expect(bucketLabel(10, 5)).toBe('≤10')
    expect(bucketLabel(null, 500)).toBe('>500')
  })
})
