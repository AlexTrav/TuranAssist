<script setup lang="ts">
import { useI18n } from 'vue-i18n'

// короткие запросы в трёх конфигурациях сервиса: A – только модель, B – + цена программы и уточнение темы,
// C – + умный поиск. Цифры – research/results/short_queries.json (make -C research collect-short), 34 запроса
const TOTAL = 34
const CONFIGS = [
  { key: 'A', correct: 16, clarify: 0, fallback: 17, wrong: 1 },
  { key: 'B', correct: 20, clarify: 6, fallback: 7, wrong: 1 },
  { key: 'C', correct: 25, clarify: 4, fallback: 4, wrong: 1 },
] as const
const PARTS = [
  { key: 'correct', label: 'about.shortCorrect', color: 'bg-primary' },
  { key: 'clarify', label: 'about.shortClarify', color: 'bg-steel' },
  { key: 'fallback', label: 'about.shortFallback', color: 'bg-gold' },
  { key: 'wrong', label: 'about.shortWrong', color: 'bg-danger' },
] as const

const { t } = useI18n()
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-4 text-xs text-muted">
      <span v-for="p in PARTS" :key="p.key" class="inline-flex items-center gap-1.5">
        <span class="h-2.5 w-2.5 rounded-sm" :class="p.color" />{{ t(p.label) }}
      </span>
    </div>
    <div class="mt-6 space-y-5">
      <div v-for="(c, i) in CONFIGS" :key="c.key" v-reveal="i">
        <div class="flex flex-wrap items-baseline justify-between gap-2">
          <span class="text-sm" :class="c.key === 'C' ? 'font-semibold text-ink' : 'text-muted'">{{ t(`about.short_${c.key}`) }}</span>
          <span class="font-mono text-xs text-ink tabular-nums">{{ t('about.shortUseful', { n: c.correct + c.clarify, total: TOTAL }) }}</span>
        </div>
        <div class="mt-2 h-4 overflow-hidden rounded bg-sand">
          <div class="reveal-grow flex h-full" :style="{ transitionDelay: `${200 + i * 150}ms` }">
            <div v-for="p in PARTS" :key="p.key" class="h-full" :class="p.color" :style="{ width: `${(c[p.key] / TOTAL) * 100}%` }" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
