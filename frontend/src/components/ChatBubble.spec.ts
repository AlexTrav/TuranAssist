import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../i18n'
import type { Explain } from '../types'
import ChatBubble from './ChatBubble.vue'

const explain: Explain = {
  language: 'ru',
  normalized: 'сколько стоит втипо?',
  tokens: [
    { text: 'сколько', lemma: 'сколько', stopword: false },
    { text: 'стоит', lemma: 'стоить', stopword: false },
  ],
  subwords: ['▁Сколько', '▁стоит', '▁В', 'Ти', 'ПО', '?'],
  subwords_total: 6,
  classified_text: 'Сколько стоит ВТиПО?',
  context_used: false,
  top: [
    { intent: 'tuition_bachelor', probability: 0.508, e5: 0.55, tfidf: 0.34 },
    { intent: 'tuition_postgrad', probability: 0.213, e5: 0.2, tfidf: 0.26 },
  ],
  weights: { e5: 0.8, tfidf: 0.2 },
  threshold: 0.577,
  rule: 'tuition_sum',
  programs: ['computer_engineering'],
}

function mountBubble(message: Record<string, unknown>) {
  return mount(ChatBubble, { global: { plugins: [i18n], stubs: { RouterLink: { template: '<a><slot /></a>' } } }, props: { message: message as never } })
}

describe('ChatBubble', () => {
  beforeEach(() => {
    i18n.global.locale.value = 'ru' // тест не зависит от языка окружения
  })

  it('renders a recognized answer with list, links, confidence and timing', () => {
    const wrapper = mountBubble({
      id: 1, role: 'bot', recognized: true, title: 'Общежитие', confidence: 0.97, timingMs: 6.4,
      text: 'Места есть.\n- звонить +7 (727) 260 40 00\n- писать на info@turan.edu.kz', sourceUrl: 'https://turan.edu.kz/ru/x',
    })
    expect(wrapper.text()).toContain('Общежитие')
    expect(wrapper.findAll('li')).toHaveLength(2)
    const hrefs = wrapper.findAll('a').map((a) => a.attributes('href'))
    expect(hrefs).toEqual(expect.arrayContaining(['tel:+77272604000', 'mailto:info@turan.edu.kz', 'https://turan.edu.kz/ru/x']))
    expect(wrapper.text()).toContain('97')
    expect(wrapper.text()).toContain('6,4')
  })

  it('shows prices as a table instead of plain text', () => {
    const wrapper = mountBubble({
      id: 2, role: 'bot', recognized: true, title: 'Стоимость бакалавриата', confidence: 0.72, text: 'длинный текст ответа',
      prices: [{ program: 'computer_engineering', name: 'ВТиПО', rows: [{ plan: 'bachelor_4y', label: 'очная, 4 года', main: 1476600, english: null }] }],
    })
    expect(wrapper.find('table').text()).toContain('очная, 4 года')
    expect(wrapper.find('table').text()).toMatch(/1\s476\s600/)
    expect(wrapper.text()).not.toContain('длинный текст ответа')
  })

  it('opens the explanation of how the question was understood', async () => {
    const wrapper = mountBubble({ id: 3, role: 'bot', recognized: true, title: 'Стоимость', confidence: 0.72, text: 'Ответ', explain })
    expect(wrapper.text()).not.toContain('·Сколько')
    await wrapper.get('button[aria-expanded]').trigger('click')
    expect(wrapper.text()).toContain('·Сколько') // подслово с отметкой начала слова
    expect(wrapper.text()).toContain('стоить') // лемма
    expect(wrapper.text()).toContain('суммарная уверенность') // правило «программа + сумма тем стоимости»
  })

  it('emits a chosen suggestion and a rating', async () => {
    const suggestion = { intent: 'contacts', title: 'Контакты', confidence: 0.3 }
    const wrapper = mountBubble({ id: 4, role: 'bot', text: 'Не понял', recognized: false, confidence: 0.3, suggestions: [suggestion] })
    await wrapper.get('button.chip').trigger('click')
    expect(wrapper.emitted('suggest')?.[0]).toEqual([suggestion])
    await wrapper.get('button[aria-label="Полезный ответ"]').trigger('click')
    expect(wrapper.emitted('rate')?.[0]).toEqual([true])
  })

  it('shows a translated error by code', () => {
    const wrapper = mountBubble({ id: 5, role: 'bot', text: '', error: 'rate_limited' })
    expect(wrapper.text()).toContain('Слишком много запросов')
  })
})
