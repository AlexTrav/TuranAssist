import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../i18n'
import KnowledgeView from './KnowledgeView.vue'

const { knowledge, intents, search } = vi.hoisted(() => ({ knowledge: vi.fn(), intents: vi.fn(), search: vi.fn() }))
vi.mock('../api/client', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/client')>()
  return { ...original, api: { knowledge, intents, search } }
})

const item = (id: string, group: string, title: string, answer: string) => ({ id, group, title, answer, source_url: null })

afterEach(() => vi.useRealTimers())

describe('KnowledgeView', () => {
  it('finds topics by meaning after a pause and marks them', async () => {
    vi.useFakeTimers()
    i18n.global.locale.value = 'ru'
    intents.mockResolvedValue([])
    knowledge.mockResolvedValue([
      item('library', 'student_life', 'Библиотека', 'Читальный зал открыт с 9:00.'),
      item('dormitory', 'student_life', 'Общежитие', 'Места в Доме студентов…'),
      item('contacts', 'about', 'Контакты', 'Приёмная комиссия: +7 (727) 260 40 00'),
    ])
    search.mockResolvedValue([{ id: 'dormitory', score: 1.48 }])
    const wrapper = mount(KnowledgeView, { global: { plugins: [i18n], stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    await flushPromises()
    await wrapper.get('input[type=search]').setValue('общага')
    // по тексту «общага» не встречается – пока сервер не ответил, тем нет
    expect(wrapper.findAll('li')).toHaveLength(0)
    await vi.advanceTimersByTimeAsync(400)
    await flushPromises()
    expect(search).toHaveBeenCalledWith('общага')
    const found = wrapper.findAll('li')
    expect(found).toHaveLength(1)
    expect(found[0].text()).toContain('Общежитие')
    expect(found[0].text()).toContain('по смыслу')
  })
})
