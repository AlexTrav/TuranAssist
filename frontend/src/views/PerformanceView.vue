<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowTrendingUpIcon,
  BoltIcon,
  CircleStackIcon,
  ClockIcon,
  CpuChipIcon,
  RocketLaunchIcon,
  SignalIcon,
  CheckCircleIcon,
} from '@heroicons/vue/24/outline'
import LatencyChart from '../components/LatencyChart.vue'
import MetricCard from '../components/MetricCard.vue'
import { useLiveMetrics } from '../composables/useLiveMetrics'
import type { AppLocale } from '../types'
import { formatDuration, formatNumber, formatPercent } from '../utils/format'

const { t, locale } = useI18n()
const { metrics, error } = useLiveMetrics(3000)
const lang = computed(() => locale.value as AppLocale)
const RENDER_MEMORY_MB = 512 // лимит памяти бесплатного Render

const ms = (v: number | null | undefined) => (v === null || v === undefined ? '–' : `${formatNumber(v, lang.value)} ${t('units.ms')}`)
const total = computed(() => metrics.value?.latency_ms.total ?? null)
const memoryShare = computed(() => Math.min((metrics.value?.memory_rss_mb ?? 0) / RENDER_MEMORY_MB, 1))
const units = computed(() => ({ h: t('units.h'), m: t('units.m'), s: t('units.s') }))
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-12">
    <div class="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-50">{{ t('performance.title') }}</h1>
        <p class="mt-2 max-w-2xl text-slate-500 dark:text-slate-400">{{ t('performance.subtitle') }}</p>
      </div>
      <span class="inline-flex items-center gap-2 text-sm" :class="error ? 'text-red-500' : 'text-emerald-600 dark:text-emerald-400'">
        <span class="h-2.5 w-2.5 rounded-full" :class="error ? 'bg-red-500' : 'animate-pulse bg-emerald-500'" />
        {{ error ? t('performance.offline') : t('performance.live') }}
      </span>
    </div>

    <p v-if="metrics && !metrics.requests_total" class="mt-6 rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-800 dark:bg-brand-900/40 dark:text-brand-200">
      {{ t('performance.noRequests') }}
      <RouterLink to="/chat" class="font-semibold underline">{{ t('performance.goChat') }}</RouterLink>
    </p>

    <div class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard :icon="BoltIcon" :label="t('performance.p50')" :value="ms(total?.p50)" :hint="t('performance.p50Hint')" accent />
      <MetricCard :icon="ArrowTrendingUpIcon" :label="t('performance.p95')" :value="ms(total?.p95)" :hint="t('performance.p95Hint')" />
      <MetricCard :icon="SignalIcon" :label="t('performance.p99')" :value="ms(total?.p99)" :hint="t('performance.p99Hint')" />
      <MetricCard
        :icon="CheckCircleIcon"
        :label="t('performance.recognized')"
        :value="metrics?.recognized_share != null ? formatPercent(metrics.recognized_share, lang) : '–'"
        :hint="t('performance.recognizedHint')"
      />
    </div>

    <div class="mt-4 grid gap-4 lg:grid-cols-3">
      <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2 dark:border-slate-800 dark:bg-slate-900">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold text-slate-900 dark:text-slate-50">{{ t('performance.chartTitle') }}</h2>
          <span class="text-xs text-slate-400">{{ t('performance.chartLegend') }}</span>
        </div>
        <div class="mt-6">
          <LatencyChart v-if="metrics?.recent.length" :points="metrics.recent" :p95="total?.p95" :unit="t('units.ms')" />
          <p v-else class="py-16 text-center text-sm text-slate-400">{{ t('performance.chartEmpty') }}</p>
        </div>
      </div>

      <div class="space-y-4">
        <MetricCard :icon="CpuChipIcon" :label="t('performance.breakdown')" :value="ms(metrics?.latency_ms.model?.p50)" :hint="t('performance.breakdownHint')">
          <div class="mt-3 space-y-1 text-sm text-slate-600 dark:text-slate-300">
            <div class="flex justify-between"><span>e5 (ONNX int8)</span><span class="tabular-nums">{{ ms(metrics?.latency_ms.e5?.p50) }}</span></div>
            <div class="flex justify-between"><span>TF-IDF</span><span class="tabular-nums">{{ ms(metrics?.latency_ms.tfidf?.p50) }}</span></div>
          </div>
        </MetricCard>
        <MetricCard
          :icon="CircleStackIcon"
          :label="t('performance.memory')"
          :value="metrics?.memory_rss_mb ? `${formatNumber(metrics.memory_rss_mb, lang, 0)} / ${RENDER_MEMORY_MB} ${t('units.mb')}` : '–'"
          :hint="t('performance.memoryHint')"
        >
          <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div class="h-full rounded-full bg-brand-500 transition-all" :style="{ width: `${memoryShare * 100}%` }" />
          </div>
        </MetricCard>
      </div>
    </div>

    <div class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard :icon="RocketLaunchIcon" :label="t('performance.coldStart')" :value="metrics?.model_load_seconds != null ? `${formatNumber(metrics.model_load_seconds, lang)} ${t('units.s')}` : '–'" :hint="t('performance.coldStartHint')" />
      <MetricCard :icon="ClockIcon" :label="t('performance.uptime')" :value="metrics ? formatDuration(metrics.uptime_seconds, units) : '–'" :hint="t('performance.uptimeHint')" />
      <MetricCard :icon="SignalIcon" :label="t('performance.requests')" :value="metrics ? String(metrics.requests_total) : '–'" :hint="t('performance.requestsHint', { n: metrics?.requests_last_minute ?? 0 })" />
      <MetricCard :icon="BoltIcon" :label="t('performance.rateLimited')" :value="metrics ? String(metrics.rate_limited_total) : '–'" :hint="t('performance.rateLimitedHint')" />
    </div>

    <p class="mt-8 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{{ t('performance.note') }}</p>
  </div>
</template>
