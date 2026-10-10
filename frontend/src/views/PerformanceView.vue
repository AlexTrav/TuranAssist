<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowTrendingUpIcon, BoltIcon, CircleStackIcon, HandThumbUpIcon, RocketLaunchIcon, SignalIcon } from '@heroicons/vue/24/outline'
import LatencyChart from '../components/LatencyChart.vue'
import MetricCard from '../components/MetricCard.vue'
import BenchmarkPanel from '../components/perf/BenchmarkPanel.vue'
import HistogramChart from '../components/perf/HistogramChart.vue'
import RulesPanel from '../components/perf/RulesPanel.vue'
import SlaRing from '../components/perf/SlaRing.vue'
import { useBenchmark } from '../composables/useBenchmark'
import { useCountUp } from '../composables/useCountUp'
import { useLiveMetrics } from '../composables/useLiveMetrics'
import type { AppLocale, RecentRequest } from '../types'
import { formatDuration, formatNumber, formatPercent } from '../utils/format'

const { t, locale } = useI18n()
const { metrics, error } = useLiveMetrics(3000)
const { result: bench, when: benchWhen, load: loadBench } = useBenchmark()
const lang = computed(() => locale.value as AppLocale)
const RENDER_MEMORY_MB = 512 // лимит памяти бесплатного Render
onMounted(loadBench)

// после пробуждения сервера живых запросов ещё нет – вместо пустых графиков показываем последний нагрузочный тест
const snapshot = computed(() => (metrics.value && !metrics.value.requests_total && bench.value ? bench.value : null))
const snapshotPoints = computed<RecentRequest[]>(() =>
  (snapshot.value?.series ?? []).map((v, i) => ({ ts: i, total_ms: v, model_ms: v, recognized: true })),
)

const total = computed(() => snapshot.value?.latency_ms ?? metrics.value?.latency_ms.total ?? null)
const sla = computed(() => snapshot.value?.sla ?? metrics.value?.sla ?? null)
// числа плавно «досчитываются» к новому значению при каждом обновлении
const p50 = useCountUp(computed(() => total.value?.p50 ?? null))
const p95 = useCountUp(computed(() => total.value?.p95 ?? null))
const perMinute = useCountUp(computed(() => metrics.value?.requests_last_minute ?? null))
const memory = useCountUp(computed(() => metrics.value?.memory_rss_mb ?? null))

const fmt = (v: number | null | undefined, digits = 1) => (v == null ? '–' : formatNumber(v, lang.value, digits))
const units = computed(() => ({ h: t('units.h'), m: t('units.m'), s: t('units.s') }))
const memoryShare = computed(() => Math.min((metrics.value?.memory_rss_mb ?? 0) / RENDER_MEMORY_MB, 1))

// разбивка медианы ответа: e5, TF-IDF и всё остальное (сеть внутри сервиса, сериализация, логика ответа)
const breakdown = computed(() => {
  const l = metrics.value?.latency_ms
  if (!l?.total || !l.e5 || !l.tfidf) return null
  const e5 = l.e5.p50
  const tfidf = l.tfidf.p50
  const other = Math.max(l.total.p50 - e5 - tfidf, 0)
  const sum = e5 + tfidf + other || 1
  return [
    { key: 'e5', label: 'e5 (ONNX int8)', value: e5, share: e5 / sum, color: 'bg-primary' },
    { key: 'tfidf', label: 'TF-IDF', value: tfidf, share: tfidf / sum, color: 'bg-steel' },
    { key: 'other', label: t('performance.other'), value: other, share: other / sum, color: 'bg-gold' },
  ]
})
const feedbackTotal = computed(() => (metrics.value ? metrics.value.feedback.useful + metrics.value.feedback.not_useful : 0))
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6">
    <div class="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="eyebrow animate-rise">{{ t('performance.eyebrow') }}</p>
        <h1 class="display-title animate-rise mt-3 text-4xl sm:text-5xl" style="animation-delay: 60ms">{{ t('performance.title') }}</h1>
        <p class="animate-rise mt-4 max-w-2xl text-lg text-muted" style="animation-delay: 120ms">{{ t('performance.subtitle') }}</p>
      </div>
      <div class="animate-rise flex flex-col items-start gap-1 sm:items-end" style="animation-delay: 180ms">
        <span class="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-medium" :class="error ? 'text-danger' : 'text-success'">
          <span class="h-2 w-2 rounded-full" :class="error ? 'bg-danger' : 'live-dot bg-success'" />
          {{ error ? t('performance.offline') : t('performance.live') }}
        </span>
        <span v-if="metrics" class="font-mono text-xs text-faint">{{ t('performance.uptime', { value: formatDuration(metrics.uptime_seconds, units) }) }}</span>
      </div>
    </div>

    <div v-if="metrics && !metrics.requests_total" class="animate-rise mt-8 rounded-2xl border border-primary/30 bg-primary-soft px-5 py-4 text-sm text-ink">
      {{ snapshot ? t('performance.snapshot') : t('performance.noRequests') }}
      <RouterLink to="/chat" class="link ml-1">{{ t('performance.goChat') }}</RouterLink>
      <p v-if="snapshot" class="mt-1.5 font-mono text-xs text-muted">{{ benchWhen }}</p>
    </div>

    <!-- ключевые показатели -->
    <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        v-reveal="0"
        :icon="BoltIcon"
        :label="t('performance.p50')"
        :value="fmt(p50)"
        :unit="t('units.ms')"
        :hint="snapshot ? t('performance.snapshotTag') : t('performance.p50Hint')"
        accent
      />
      <MetricCard
        v-reveal="1"
        :icon="ArrowTrendingUpIcon"
        :label="t('performance.p95')"
        :value="fmt(p95)"
        :unit="t('units.ms')"
        :hint="snapshot ? t('performance.snapshotTag') : t('performance.p95Hint')"
      />
      <div v-reveal="2" class="card flex items-center gap-4 p-5">
        <SlaRing :share="sla?.share ?? null" :size="88" />
        <div>
          <div class="text-sm font-medium text-muted">{{ t('performance.sla') }}</div>
          <div class="mt-1 text-xs text-faint">{{ t('performance.slaHint', { target: sla?.target_ms ?? 100 }) }}</div>
          <div v-if="snapshot" class="mt-1 text-xs text-faint">{{ t('performance.snapshotTag') }}</div>
        </div>
      </div>
      <MetricCard
        v-reveal="3"
        :icon="SignalIcon"
        :label="t('performance.perMinute')"
        :value="perMinute == null ? '–' : String(Math.round(perMinute))"
        :hint="t('performance.perMinuteHint', { n: metrics?.requests_total ?? 0 })"
      />
    </div>

    <!-- живой график и гистограмма -->
    <div class="mt-4 grid gap-4 lg:grid-cols-[1.6fr_1fr]">
      <div v-reveal class="card p-5 sm:p-6">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="font-display font-semibold text-ink">{{ t('performance.chartTitle') }}</h2>
          <div class="flex flex-wrap items-center gap-3 text-xs text-muted">
            <span v-if="snapshot" class="inline-flex items-center gap-1.5"><span class="h-2 w-2 rounded-full bg-primary" />{{ t('performance.snapshotLegend') }}</span>
            <template v-else>
              <span class="inline-flex items-center gap-1.5"><span class="h-2 w-2 rounded-full bg-primary" />{{ t('performance.chartLegendOk') }}</span>
              <span class="inline-flex items-center gap-1.5"><span class="h-2 w-2 rounded-full bg-gold" />{{ t('performance.chartLegendMiss') }}</span>
              <span class="inline-flex items-center gap-1.5"><span class="h-2 w-2 rounded-full bg-steel" />{{ t('performance.chartLegendClarify') }}</span>
            </template>
            <span class="inline-flex items-center gap-1.5"><span class="w-4 border-t-2 border-dashed border-gold" />{{ t('performance.chartLegendP95') }}</span>
          </div>
        </div>
        <div class="mt-6">
          <LatencyChart v-if="snapshot" :points="snapshotPoints" :p95="total?.p95" :unit="t('units.ms')" />
          <LatencyChart v-else-if="metrics?.recent.length" :points="metrics.recent" :p95="total?.p95" :unit="t('units.ms')" />
          <p v-else class="py-20 text-center text-sm text-faint">{{ t('performance.chartEmpty') }}</p>
        </div>
      </div>
      <div v-reveal="1" class="card p-5 sm:p-6">
        <h2 class="font-display font-semibold text-ink">{{ t('performance.histTitle') }}</h2>
        <p class="mt-1 text-xs text-faint">
          {{ snapshot ? t('performance.snapshotHist', { n: snapshot.n }) : t('performance.histHint', { n: metrics?.window ?? 0 }) }}
        </p>
        <div class="mt-6">
          <HistogramChart v-if="snapshot" :buckets="snapshot.histogram" :target="snapshot.sla.target_ms" />
          <HistogramChart v-else-if="metrics?.window" :buckets="metrics.histogram" :target="metrics.sla.target_ms" />
          <p v-else class="py-16 text-center text-sm text-faint">{{ t('performance.chartEmpty') }}</p>
        </div>
      </div>
    </div>

    <!-- из чего складывается ответ, память, загрузка модели, оценки -->
    <div class="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div v-reveal class="card p-5 md:col-span-2">
        <div class="flex items-baseline justify-between">
          <h2 class="text-sm font-medium text-muted">{{ t('performance.breakdown') }}</h2>
          <span class="text-xs text-faint">{{ t('performance.breakdownHint') }}</span>
        </div>
        <template v-if="breakdown">
          <div class="mt-4 flex h-3 overflow-hidden rounded-full bg-sand">
            <div v-for="part in breakdown" :key="part.key" :class="part.color" class="h-full transition-all duration-700 ease-(--ease-out-quint)" :style="{ width: `${part.share * 100}%` }" />
          </div>
          <ul class="mt-4 grid grid-cols-3 gap-3">
            <li v-for="part in breakdown" :key="part.key">
              <span class="flex items-center gap-1.5 text-xs text-muted"><span class="h-2 w-2 rounded-full" :class="part.color" />{{ part.label }}</span>
              <span class="mt-1 block font-mono text-lg text-ink tabular-nums">{{ fmt(part.value, 2) }}</span>
            </li>
          </ul>
        </template>
        <p v-else class="mt-4 text-sm text-faint">–</p>
      </div>
      <MetricCard v-reveal="1" :icon="CircleStackIcon" :label="t('performance.memory')" :value="fmt(memory, 0)" :unit="`/ ${RENDER_MEMORY_MB} ${t('units.mb')}`" :hint="t('performance.memoryHint')">
        <div class="mt-3 h-2 overflow-hidden rounded-full bg-sand">
          <div class="h-full rounded-full transition-all duration-700" :class="memoryShare > 0.85 ? 'bg-danger' : 'bg-primary'" :style="{ width: `${memoryShare * 100}%` }" />
        </div>
      </MetricCard>
      <MetricCard
        v-reveal="2"
        :icon="RocketLaunchIcon"
        :label="t('performance.coldStart')"
        :value="fmt(metrics?.model_load_seconds)"
        :unit="t('units.s')"
        :hint="t('performance.coldStartHint')"
      />
      <MetricCard
        v-reveal="0"
        :icon="HandThumbUpIcon"
        :label="t('performance.feedback')"
        :value="feedbackTotal ? formatPercent(metrics!.feedback.useful / feedbackTotal, lang) : '–'"
        :hint="feedbackTotal ? t('performance.feedbackHint', { up: metrics!.feedback.useful, down: metrics!.feedback.not_useful }) : t('performance.noFeedback')"
      />
      <MetricCard
        v-reveal="1"
        :icon="SignalIcon"
        :label="t('performance.recognized')"
        :value="metrics?.recognized_share != null ? formatPercent(metrics.recognized_share, lang) : '–'"
        :hint="t('performance.recognizedHint')"
      >
        <p class="mt-2 font-mono text-[11px] text-faint">{{ t('performance.rateLimited', { n: metrics?.rate_limited_total ?? 0 }) }}</p>
      </MetricCard>
    </div>

    <!-- как бот ответил: модель, цена программы, умный поиск, уточнение, «не понял» -->
    <RulesPanel v-reveal class="mt-4" :rules="metrics?.rules ?? null" :context="metrics?.context_total ?? 0" />

    <div v-reveal class="mt-10">
      <BenchmarkPanel />
    </div>

    <p class="mt-8 max-w-4xl text-sm leading-relaxed text-faint">{{ t('performance.note') }}</p>
  </div>
</template>
