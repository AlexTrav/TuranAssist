export type AppLocale = 'ru' | 'kk' | 'en'

// подсказка «возможно, вы имели в виду», когда бот не уверен
export interface Suggestion {
  intent: string
  title: string
  confidence: number
}

// ответ POST /api/chat
export interface ChatResponse {
  recognized: boolean // false – уверенность ниже порога, бот честно отвечает «не понял»
  intent: string | null
  title: string | null
  confidence: number
  answer: string
  source_url: string | null
  suggestions: Suggestion[]
  lang: AppLocale
  timing_ms: Record<string, number> // tfidf, e5, model, total
}

// ответ GET /api/answer/{intent}
export interface IntentAnswer {
  intent: string
  title: string
  answer: string
  source_url: string | null
  lang: AppLocale
}

export interface IntentInfo {
  id: string
  group: string
  title: Record<AppLocale, string>
}

// группа тем, GET /api/intents
export interface GroupInfo {
  id: string
  title: Record<AppLocale, string>
  intents: IntentInfo[]
}

// доля с 95% доверительным интервалом Уилсона
export interface Proportion {
  value: number
  ci95: [number, number]
  n: number
  successes: number
}

export interface ModelRow {
  cv_accuracy: number
  threshold: number
  latency_p50_ms: number | null
  test: Proportion
  ood_rejected: Proportion
  external: Proportion
  scenarios: Proportion
}

// сводка качества моделей, GET /api/model-info
export interface ModelInfo {
  name: string
  threshold: number
  weight_e5: number
  intents: number
  encoder: string
  comparison: { tfidf: ModelRow; e5: ModelRow; ensemble: ModelRow }
}

export interface Percentiles {
  p50: number
  p95: number
  p99: number
  max: number
}

export interface RecentRequest {
  ts: number // unix-время в секундах
  total_ms: number
  model_ms: number
  recognized: boolean
}

// живые метрики сервиса, GET /api/metrics
export interface LiveMetrics {
  uptime_seconds: number
  model_load_seconds: number | null
  warmup_ms: number | null
  memory_rss_mb: number | null
  requests_total: number
  recognized_share: number | null
  rate_limited_total: number
  requests_last_minute: number
  window: number
  latency_ms: {
    total: Percentiles | null
    model: Percentiles | null
    tfidf: Percentiles | null
    e5: Percentiles | null
  }
  recent: RecentRequest[]
}
