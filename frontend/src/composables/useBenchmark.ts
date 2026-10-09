import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, ApiError } from '../api/client'
import type { AppLocale, BenchmarkResult } from '../types'
import { formatDate, formatDuration } from '../utils/format'

// последний нагрузочный тест – общий для панели теста и для графиков страницы «Производительность»:
// пока после пробуждения сервера не было живых вопросов, графики показывают этот тест, а не пустоту
const result = ref<BenchmarkResult | null>(null)
const running = ref(false)
const error = ref('')
const cached = ref(false) // нажали во время кулдауна – сервер вернул прошлый результат
const nextRunIn = ref(0) // секунд до следующего запуска (общий кулдаун сервера)
let ticker: ReturnType<typeof setInterval> | undefined
const receivedAt = ref(0) // когда пришёл результат – возраст живого теста растёт и после ответа сервера
const clock = ref(Date.now())
let clockTimer: ReturnType<typeof setInterval> | undefined
let loading: Promise<void> | null = null

function applyCooldown(seconds: number) {
  nextRunIn.value = Math.ceil(seconds)
  clearInterval(ticker)
  if (nextRunIn.value > 0) {
    ticker = setInterval(() => {
      nextRunIn.value = Math.max(0, nextRunIn.value - 1)
      if (nextRunIn.value === 0) clearInterval(ticker)
    }, 1000)
  }
}

export function useBenchmark() {
  function load(): Promise<void> {
    loading ??= api
      .lastBenchmark()
      .then((data) => {
        result.value = data
        receivedAt.value = Date.now()
        if (data) applyCooldown(data.next_run_in)
      })
      .catch(() => {})
      .finally(() => {
        loading = null
      })
    return loading
  }

  async function run() {
    running.value = true
    error.value = ''
    cached.value = false
    try {
      const data = await api.benchmark()
      result.value = data
      receivedAt.value = Date.now()
      cached.value = !!data.cached
      applyCooldown(data.next_run_in)
    } catch (err) {
      error.value = err instanceof ApiError ? err.code : 'network'
    } finally {
      running.value = false
    }
  }

  clockTimer ??= setInterval(() => (clock.value = Date.now()), 5000)
  const isReference = computed(() => result.value?.source === 'reference')
  // сколько секунд назад прошёл живой тест – с учётом времени, прошедшего после ответа сервера
  const ageSeconds = computed(() =>
    result.value?.age_seconds == null ? null : result.value.age_seconds + Math.max(0, clock.value - receivedAt.value) / 1000,
  )
  // когда получен показанный результат: «тест запущен 3 мин назад» или «сохранённый замер на Render от …»
  const { t, locale } = useI18n()
  const when = computed(() => {
    const r = result.value
    if (!r) return ''
    const lang = locale.value as AppLocale
    if (r.source === 'reference') {
      return t('performance.benchReference', { date: r.measured_at ? formatDate(r.measured_at, lang) : '–' })
    }
    const age = ageSeconds.value ?? 0
    const units = { h: t('units.h'), m: t('units.m'), s: t('units.s') }
    return age < 60 ? t('performance.benchJustNow') : t('performance.benchAgo', { value: formatDuration(age, units) })
  })
  return { result, running, error, cached, nextRunIn, isReference, ageSeconds, when, load, run }
}
