import type { AppLocale, ChatResponse, GroupInfo, IntentAnswer, LiveMetrics, ModelInfo } from '../types'

// в Docker-сборке пусто (тот же домен, nginx проксирует /api), в dev и на GitHub Pages – адрес бэкенда
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// бесплатный Render засыпает и просыпается около минуты – ждём дольше, чем обычно
const DEFAULT_TIMEOUT_MS = 70_000

// ошибка API с машинным кодом (rate_limited, empty_text, network, timeout…) – текст переводит интерфейс
export class ApiError extends Error {
  code: string
  status: number

  constructor(code: string, status = 0) {
    super(code)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, { ...init, signal: controller.signal })
  } catch (err) {
    throw new ApiError((err as Error).name === 'AbortError' ? 'timeout' : 'network')
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) {
    let code = `http_${res.status}`
    try {
      const data = await res.json()
      if (data?.detail?.code) code = data.detail.code // бэкенд отвечает {"detail": {"code", "message"}}
    } catch {
      // тело не JSON – остаётся код по HTTP-статусу
    }
    throw new ApiError(code, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  // lang не передаём: бэкенд отвечает на языке вопроса, как и Telegram-бот
  chat: (text: string) =>
    request<ChatResponse>('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }),
  answer: (intent: string, lang: AppLocale) =>
    request<IntentAnswer>(`/api/answer/${encodeURIComponent(intent)}?lang=${lang}`),
  intents: () => request<GroupInfo[]>('/api/intents'),
  modelInfo: () => request<ModelInfo>('/api/model-info'),
  metrics: () => request<LiveMetrics>('/api/metrics', {}, 10_000),
  health: (timeoutMs = DEFAULT_TIMEOUT_MS) => request<{ status: string }>('/api/health', {}, timeoutMs),
}
