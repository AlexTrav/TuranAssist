export type AppLocale = 'ru' | 'kk' | 'en'
export type Localized = Record<AppLocale, string>

// подсказка «возможно, вы имели в виду», когда бот не уверен
export interface Suggestion {
  intent: string
  title: string
  confidence: number
}

// тема последнего ответа: сервер ничего не хранит, клиент присылает её обратно
export interface ChatContext {
  text: string
  intent: string
}

// цены одной программы по формам обучения – таблица в ответе чата
export interface PriceRow {
  plan: string
  label: string
  main: number // казахское или русское отделение, тенге за год
  english: number | null // английское отделение
}
export interface PriceCard {
  program: string
  name: string
  rows: PriceRow[]
}

// разбор вопроса по ступеням конвейера – панель «Как бот понял вопрос»
export interface ExplainToken {
  text: string
  lemma: string
  stopword: boolean
}
export interface ExplainCandidate {
  intent: string
  probability: number // ансамбль
  e5: number
  tfidf: number
}
// model – порог модели, tuition_sum – сумма тем стоимости, program – программа и слова о цене, search – умный поиск,
// clarify – короткий запрос на несколько тем, fallback – «не понял», chosen – тему выбрали кнопкой
export type DecisionRule = 'model' | 'tuition_sum' | 'program' | 'search' | 'clarify' | 'fallback' | 'chosen'
export interface Explain {
  language: AppLocale
  normalized: string
  tokens: ExplainToken[]
  subwords: string[]
  subwords_total: number
  classified_text: string
  context_used: boolean
  top: ExplainCandidate[]
  weights: { e5: number; tfidf: number }
  threshold: number
  rule: DecisionRule
  decisive?: number | null // уверенность, по которой принято решение (сумма тем у tuition_sum, program, clarify)
  // правило search: тема, близость вопроса к её названию, отрыв от следующей темы и общие слова
  search?: { intent: string; score: number; margin: number; shared: string[] } | null
  programs: string[]
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
  programs?: string[] // образовательные программы, найденные в вопросе о стоимости
  context_used?: boolean // вопрос понят как уточнение предыдущего («а в магистратуре?»)
  clarify?: boolean // короткий запрос на несколько тем – бот просит выбрать тему из suggestions
  context?: ChatContext | null // вернуть серверу со следующим вопросом
  prices?: PriceCard[]
  explain?: Explain | null
}

// ответ GET /api/answer/{intent}
export interface IntentAnswer {
  intent: string
  title: string
  answer: string
  source_url: string | null
  lang: AppLocale
  explain?: Explain | null // разбор названия выбранной темы (rule = chosen)
}

export interface IntentInfo {
  id: string
  group: string
  title: Localized
}

// группа тем, GET /api/intents
export interface GroupInfo {
  id: string
  title: Localized
  intents: IntentInfo[]
}

// тема с ответом на одном языке, GET /api/knowledge
export interface KnowledgeItem {
  id: string
  group: string
  title: string
  answer: string
  source_url: string | null
}

// справочник цен, GET /api/tuition
export type Level = 'bachelor' | 'postgrad'
export interface TuitionPlan {
  id: string
  level: Level
  label: Localized
}
export interface TuitionPrice {
  plan: string
  main: number
  english?: number
}
export interface TuitionProgram {
  id: string
  name: Localized
  prices: TuitionPrice[]
}
export interface TuitionCatalog {
  plans: TuitionPlan[]
  programs: TuitionProgram[]
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

export interface HistogramBucket {
  le: number | null // верхняя граница корзины, мс; null – всё, что дольше
  count: number
}

export interface Sla {
  target_ms: number
  share: number | null // доля ответов быстрее цели
}

export interface RecentRequest {
  ts: number // unix-время в секундах
  total_ms: number
  model_ms: number
  recognized: boolean
  rule?: DecisionRule // правило ответа; у точек нагрузочного теста его нет
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
  rules: Record<string, number> // сколько ответов дало каждое правило с запуска сервера
  context_total: number // уточнения, понятые вместе с предыдущим вопросом
  requests_last_minute: number
  window: number
  latency_ms: {
    total: Percentiles | null
    model: Percentiles | null
    tfidf: Percentiles | null
    e5: Percentiles | null
  }
  histogram: HistogramBucket[]
  sla: Sla
  feedback: { useful: number; not_useful: number }
  recent: RecentRequest[]
}

// результат нагрузочного теста, POST /api/benchmark
export interface BenchmarkResult {
  n: number
  seconds: number
  throughput_rps: number
  latency_ms: Percentiles
  histogram: HistogramBucket[]
  sla: Sla
  series: number[]
  source: 'live' | 'reference' // живой тест или сохранённый замер на Render (после пробуждения сервера)
  measured_at: string | null // дата сохранённого замера
  age_seconds: number | null // сколько секунд назад прошёл живой тест
  next_run_in: number // секунд до следующего запуска – общий кулдаун сервера
  cooldown_seconds: number
  cached?: boolean // запуск во время кулдауна – сервер вернул прошлый результат
}

// тема из умного поиска, GET /api/search: ранг – вероятность модели плюс близость к названию темы
export interface SearchResult {
  id: string
  score: number
}
