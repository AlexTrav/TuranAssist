import { nextTick } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'

// vi.mock поднимается в начало файла – моки объявляем через vi.hoisted, иначе они ещё не созданы
const { chat, answer } = vi.hoisted(() => ({ chat: vi.fn(), answer: vi.fn() }))
vi.mock('../api/client', async (importOriginal) => {
  const original = await importOriginal<typeof import('../api/client')>()
  return { ...original, api: { chat, answer } }
})

describe('useChat', () => {
  beforeEach(() => {
    localStorage.clear()
    chat.mockReset()
    answer.mockReset()
    vi.resetModules() // singleton-состояние модуля – заново для каждого теста
  })

  it('adds the question and the bot answer with metadata', async () => {
    chat.mockResolvedValue({
      recognized: true, intent: 'dormitory', title: 'Общежитие', confidence: 0.97, answer: 'Места в Доме студентов…',
      source_url: 'https://turan.edu.kz/ru/x', suggestions: [], lang: 'ru', timing_ms: { total: 6.4 },
    })
    const { useChat } = await import('./useChat')
    const { messages, send } = useChat()
    await send('  Есть ли общежитие?  ')
    expect(chat).toHaveBeenCalledWith('Есть ли общежитие?')
    expect(messages.value.map((m) => m.role)).toEqual(['user', 'bot'])
    expect(messages.value[1]).toMatchObject({ recognized: true, sourceUrl: 'https://turan.edu.kz/ru/x', timingMs: 6.4 })
  })

  it('stores an error code instead of throwing', async () => {
    chat.mockRejectedValue(new ApiError('rate_limited', 429))
    const { useChat } = await import('./useChat')
    const { messages, send } = useChat()
    await send('привет')
    expect(messages.value[1]).toMatchObject({ role: 'bot', error: 'rate_limited' })
  })

  it('ignores empty questions and answers a chosen suggestion', async () => {
    answer.mockResolvedValue({ intent: 'contacts', title: 'Контакты', answer: 'Главный корпус…', source_url: null, lang: 'ru' })
    const { useChat } = await import('./useChat')
    const { messages, send, choose } = useChat()
    await send('   ')
    expect(messages.value).toHaveLength(0)
    await choose({ intent: 'contacts', title: 'Контакты', confidence: 0.3 }, 'ru')
    expect(answer).toHaveBeenCalledWith('contacts', 'ru')
    expect(messages.value.map((m) => m.text)).toEqual(['Контакты', 'Главный корпус…'])
  })

  it('persists history to localStorage and restores it', async () => {
    chat.mockResolvedValue({ recognized: false, intent: null, title: null, confidence: 0.2, answer: 'Не понял', source_url: null, suggestions: [], lang: 'ru', timing_ms: { total: 5 } })
    const first = await import('./useChat')
    await first.useChat().send('фыва')
    await nextTick()
    vi.resetModules()
    const second = await import('./useChat')
    expect(second.useChat().messages.value).toHaveLength(2)
  })
})
