import { ref, watch } from 'vue'
import { api, ApiError } from '../api/client'
import type { AppLocale, ChatContext, Explain, PriceCard, Suggestion } from '../types'

export interface ChatMessage {
  id: number
  role: 'user' | 'bot'
  text: string
  intent?: string | null
  recognized?: boolean
  title?: string | null
  confidence?: number
  sourceUrl?: string | null
  suggestions?: Suggestion[]
  timingMs?: number
  contextUsed?: boolean // ответ дан с учётом предыдущего вопроса
  prices?: PriceCard[] // цены найденных программ – таблица под ответом
  explain?: Explain | null // разбор вопроса – панель «Как бот понял»
  feedback?: 'up' | 'down' // оценка пользователя
  error?: string // код ошибки API – текст подставляет интерфейс на текущем языке
}

export const CHAT_STORAGE_KEY = 'turanassist-chat'
export const MAX_MESSAGES = 60 // история в браузере ограничена, чтобы localStorage не разрастался

function load(): ChatMessage[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(CHAT_STORAGE_KEY) ?? '[]')
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

// модульный singleton: история не теряется при переходах между страницами
const messages = ref<ChatMessage[]>(load())
const pending = ref(false)
// тема последнего ответа для уточнений «а в магистратуре?» – только в памяти вкладки, не в localStorage
let context: ChatContext | null = null
let nextId = messages.value.reduce((max, m) => Math.max(max, m.id), 0) + 1

watch(
  messages,
  (value) => {
    try {
      localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(value.slice(-MAX_MESSAGES)))
    } catch {
      // не критично – история просто не сохранится
    }
  },
  { deep: true },
)

function push(message: Omit<ChatMessage, 'id'>) {
  messages.value.push({ id: nextId++, ...message })
  if (messages.value.length > MAX_MESSAGES) messages.value.splice(0, messages.value.length - MAX_MESSAGES)
}

function errorCode(err: unknown): string {
  return err instanceof ApiError ? err.code : 'network'
}

export function useChat() {
  async function send(text: string) {
    const question = text.trim()
    if (!question || pending.value) return
    push({ role: 'user', text: question })
    pending.value = true
    try {
      const res = await api.chat(question, context)
      context = res.context ?? null
      push({
        role: 'bot',
        text: res.answer,
        intent: res.intent,
        recognized: res.recognized,
        title: res.title,
        confidence: res.confidence,
        sourceUrl: res.source_url,
        suggestions: res.suggestions,
        timingMs: res.timing_ms.total,
        contextUsed: res.context_used,
        prices: res.prices ?? [],
        explain: res.explain ?? null,
      })
    } catch (err) {
      push({ role: 'bot', text: '', error: errorCode(err) })
    } finally {
      pending.value = false
    }
  }

  // нажатие на подсказку или тему – ответ по выбранной теме без классификации
  async function choose(suggestion: Pick<Suggestion, 'intent' | 'title'>, lang: AppLocale) {
    if (pending.value) return
    push({ role: 'user', text: suggestion.title })
    pending.value = true
    try {
      const res = await api.answer(suggestion.intent, lang)
      context = { text: res.title, intent: res.intent } // после выбора темы можно уточнять: «а ВТиПО?»
      push({ role: 'bot', text: res.answer, intent: res.intent, recognized: true, title: res.title, sourceUrl: res.source_url })
    } catch (err) {
      push({ role: 'bot', text: '', error: errorCode(err) })
    } finally {
      pending.value = false
    }
  }

  // оценка ответа 👍/👎: на сервер уходит только тема и оценка, без текста вопроса
  async function rate(id: number, useful: boolean) {
    const message = messages.value.find((m) => m.id === id)
    if (!message || message.feedback) return
    message.feedback = useful ? 'up' : 'down'
    try {
      await api.feedback(message.intent ?? null, useful)
    } catch {
      // оценка не критична – при ошибке сети просто не учтётся в метриках
    }
  }

  function clear() {
    messages.value = []
    context = null
  }

  return { messages, pending, send, choose, rate, clear }
}
