<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { BoltIcon, PlayIcon } from '@heroicons/vue/24/solid'
import { api, ApiError } from '../../api/client'
import type { AppLocale, BenchmarkResult } from '../../types'
import { niceMax } from '../../utils/chart'
import { formatNumber, formatPercent } from '../../utils/format'
import HistogramChart from './HistogramChart.vue'

// нагрузочный тест по кнопке: сервер прогоняет 100 фраз через модель, здесь результат «проигрывается» –
// точки-запросы появляются по одной, как шли на сервере
const BENCH_SIZE = 100 // как BENCHMARK_SIZE на бэкенде
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)

const state = ref<'idle' | 'running' | 'done' | 'error'>('idle')
const result = ref<BenchmarkResult | null>(null)
const errorCode = ref('')
const elapsed = ref(0)
let timer: ReturnType<typeof setInterval> | undefined

async function run() {
  state.value = 'running'
  elapsed.value = 0
  const started = performance.now()
  timer = setInterval(() => (elapsed.value = (performance.now() - started) / 1000), 100)
  try {
    result.value = await api.benchmark()
    state.value = 'done'
  } catch (err) {
    errorCode.value = err instanceof ApiError ? err.code : 'network'
    state.value = 'error'
  } finally {
    clearInterval(timer)
  }
}
onUnmounted(() => clearInterval(timer))

const top = computed(() => (result.value ? niceMax(result.value.latency_ms.p99 * 1.15) : 1))
const dots = computed(() =>
  (result.value?.series ?? []).map((v, i, all) => ({
    x: all.length > 1 ? (i / (all.length - 1)) * 100 : 50,
    y: 100 - (Math.min(v, top.value) / top.value) * 100,
    slow: v > (result.value?.sla.target_ms ?? Infinity),
  })),
)
const slaY = computed(() => (result.value ? 100 - (Math.min(result.value.sla.target_ms, top.value) / top.value) * 100 : 0))
const errorText = computed(() => {
  const key = `apiErrors.${errorCode.value}`
  return t(key) === key ? t('apiErrors.generic') : t(key)
})
const ms = (v: number) => `${formatNumber(v, lang.value)} ${t('units.ms')}`
</script>

<template>
  <section class="relative overflow-hidden rounded-3xl bg-[#0f172a] p-6 text-white sm:p-8 dark:bg-surface dark:ring-1 dark:ring-line">
    <div class="pointer-events-none absolute inset-0 [background-image:radial-gradient(rgba(255,255,255,0.07)_1px,transparent_1px)] [background-size:18px_18px]" aria-hidden="true" />
    <div class="relative grid gap-8 lg:grid-cols-[1fr_1.3fr]">
      <div>
        <p class="font-mono text-xs tracking-wider text-[#36baf2] uppercase">{{ t('performance.benchEyebrow') }}</p>
        <h2 class="mt-3 font-display text-2xl font-bold sm:text-3xl">{{ t('performance.benchTitle') }}</h2>
        <p class="mt-3 leading-relaxed text-white/70">{{ t('performance.benchText', { n: BENCH_SIZE }) }}</p>
        <button
          class="btn mt-6 bg-[#36baf2] text-[#0f172a] hover:bg-[#6ec1f0]"
          :disabled="state === 'running'"
          @click="run"
        >
          <PlayIcon v-if="state !== 'running'" class="h-4 w-4" />
          <BoltIcon v-else class="h-4 w-4 animate-pulse" />
          {{ state === 'running' ? t('performance.benchRunning') : state === 'done' ? t('performance.benchAgain') : t('performance.benchRun') }}
        </button>
        <p v-if="state === 'error'" class="animate-rise mt-3 text-sm text-[#f07171]">{{ errorText }}</p>

        <!-- итоговые цифры теста -->
        <dl v-if="state === 'done' && result" class="mt-8 grid grid-cols-2 gap-x-6 gap-y-5">
          <div class="animate-rise">
            <dt class="text-xs text-white/50">{{ t('performance.throughput') }}</dt>
            <dd class="mt-1 font-mono text-2xl text-[#36baf2] tabular-nums">{{ formatNumber(result.throughput_rps, lang, 0) }} <span class="text-sm text-white/50">{{ t('units.rps') }}</span></dd>
            <dd class="text-[11px] text-white/40">{{ t('performance.throughputHint') }}</dd>
          </div>
          <div class="animate-rise" style="animation-delay: 60ms">
            <dt class="text-xs text-white/50">{{ t('performance.p50') }}</dt>
            <dd class="mt-1 font-mono text-2xl tabular-nums">{{ ms(result.latency_ms.p50) }}</dd>
          </div>
          <div class="animate-rise" style="animation-delay: 120ms">
            <dt class="text-xs text-white/50">p95</dt>
            <dd class="mt-1 font-mono text-2xl tabular-nums">{{ ms(result.latency_ms.p95) }}</dd>
          </div>
          <div class="animate-rise" style="animation-delay: 180ms">
            <dt class="text-xs text-white/50">{{ t('performance.p99') }}</dt>
            <dd class="mt-1 font-mono text-2xl tabular-nums">{{ ms(result.latency_ms.p99) }}</dd>
          </div>
          <div class="animate-rise col-span-2 text-sm text-white/60" style="animation-delay: 240ms">
            {{ t('performance.benchDone', { n: result.n, s: formatNumber(result.seconds, lang, 2) }) }} ·
            {{ t('performance.benchSla', { share: formatPercent(result.sla.share ?? 0, lang, 0), target: result.sla.target_ms }) }}
          </div>
        </dl>
      </div>

      <div class="min-h-64 rounded-2xl bg-white/5 p-4 ring-1 ring-white/10">
        <!-- идёт тест: бегущая полоса и секундомер -->
        <div v-if="state === 'running'" class="flex h-full min-h-56 flex-col items-center justify-center gap-4">
          <div class="h-1.5 w-2/3 overflow-hidden rounded-full bg-white/10">
            <div class="indeterminate h-full w-1/3 rounded-full bg-[#36baf2]" />
          </div>
          <span class="font-mono text-3xl tabular-nums">{{ formatNumber(elapsed, lang, 1) }} {{ t('units.s') }}</span>
        </div>
        <!-- результат: каждая фраза – точка; жёлтые медленнее цели; затем гистограмма -->
        <div v-else-if="state === 'done' && result" class="space-y-5">
          <div class="relative h-36">
            <span class="absolute inset-x-0 border-t border-dashed border-[#ffbb00]/70" :style="{ top: `${slaY}%` }">
              <span class="absolute -top-4 right-0 font-mono text-[10px] text-[#ffbb00]">{{ result.sla.target_ms }} {{ t('units.ms') }}</span>
            </span>
            <span
              v-for="(d, i) in dots"
              :key="i"
              class="animate-pop absolute h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full"
              :class="d.slow ? 'bg-[#ffbb00]' : 'bg-[#36baf2]'"
              :style="{ left: `${d.x}%`, top: `${d.y}%`, animationDelay: `${i * 14}ms` }"
            />
            <span v-if="top !== result.sla.target_ms" class="absolute top-0 left-0 font-mono text-[10px] text-white/40">{{ top }} {{ t('units.ms') }}</span>
          </div>
          <div class="text-white [--line:rgba(255,255,255,0.12)] [--faint:rgba(255,255,255,0.45)] [--primary:#36baf2] [--gold:#ffbb00] [--ink:#ffffff] [--page:#0f172a]">
            <HistogramChart :buckets="result.histogram" :target="result.sla.target_ms" />
          </div>
        </div>
        <div v-else class="flex h-full min-h-56 items-center justify-center">
          <div class="flex items-end gap-1.5 opacity-40">
            <span v-for="h in [30, 55, 40, 80, 60, 35, 70, 45]" :key="h" class="w-3 rounded-t bg-white/40" :style="{ height: `${h}px` }" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
