import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../../i18n'
import RulesPanel from './RulesPanel.vue'

describe('RulesPanel', () => {
  beforeEach(() => {
    i18n.global.locale.value = 'ru'
  })

  it('groups price rules and shows counts, shares and follow-ups', () => {
    const rules = { model: 5, tuition_sum: 1, program: 1, search: 1, clarify: 1, fallback: 1 }
    const wrapper = mount(RulesPanel, { global: { plugins: [i18n] }, props: { rules, context: 2 } })
    const items = wrapper.findAll('li').map((li) => li.text())
    expect(items).toHaveLength(5)
    expect(items[0]).toContain('Модель уверена')
    expect(items[0]).toContain('5')
    expect(items[1]).toContain('Цена программы') // сумма интентов стоимости и программа + цена – одна группа
    expect(items[1]).toContain('2')
    expect(items[1]).toContain('20')
    expect(wrapper.text()).toContain('вопросов: 10')
    expect(wrapper.text()).toContain('предыдущим вопросом: 2')
  })

  it('shows a hint before the first questions', () => {
    const wrapper = mount(RulesPanel, { global: { plugins: [i18n] }, props: { rules: null, context: 0 } })
    expect(wrapper.findAll('li')).toHaveLength(0)
    expect(wrapper.text()).toContain('«Гранты»')
  })
})
