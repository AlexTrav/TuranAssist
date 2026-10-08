import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../i18n'
import ChatBubble from './ChatBubble.vue'

describe('ChatBubble', () => {
  beforeEach(() => {
    i18n.global.locale.value = 'ru' // тест не зависит от языка окружения
  })

  it('renders a recognized answer with source link, confidence and timing', () => {
    const wrapper = mount(ChatBubble, {
      global: { plugins: [i18n] },
      props: { message: { id: 1, role: 'bot', text: 'Ответ', recognized: true, title: 'Общежитие', confidence: 0.97, sourceUrl: 'https://turan.edu.kz/ru/x', timingMs: 6.4 } },
    })
    expect(wrapper.text()).toContain('Общежитие')
    expect(wrapper.find('a').attributes('href')).toBe('https://turan.edu.kz/ru/x')
    expect(wrapper.text()).toContain('97')
    expect(wrapper.text()).toContain('6,4')
  })

  it('emits a chosen suggestion', async () => {
    const suggestion = { intent: 'contacts', title: 'Контакты', confidence: 0.3 }
    const wrapper = mount(ChatBubble, {
      global: { plugins: [i18n] },
      props: { message: { id: 2, role: 'bot', text: 'Не понял', recognized: false, confidence: 0.3, suggestions: [suggestion] } },
    })
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('suggest')?.[0]).toEqual([suggestion])
  })

  it('shows a translated error by code', () => {
    const wrapper = mount(ChatBubble, {
      global: { plugins: [i18n] },
      props: { message: { id: 3, role: 'bot', text: '', error: 'rate_limited' } },
    })
    expect(wrapper.text()).toContain('Слишком много вопросов')
  })
})
