<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AppLocale, ModelInfo, Proportion } from '../../types'
import { formatFixed } from '../../utils/format'

// сравнение моделей по четырём наборам: полосы – доля верных ответов, «усы» – 95% интервал Уилсона
const props = defineProps<{ model: ModelInfo }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)

const MODELS = ['tfidf', 'e5', 'ensemble'] as const
const METRICS = [
  { key: 'test', label: 'about.metricTest' },
  { key: 'external', label: 'about.metricExternal' },
  { key: 'scenarios', label: 'about.metricScenarios' },
  { key: 'ood_rejected', label: 'about.metricOod' },
] as const
const COLORS = { tfidf: 'bg-steel', e5: 'bg-primary/60', ensemble: 'bg-primary' }

const groups = computed(() =>
  METRICS.map((m) => ({
    label: t(m.label),
    rows: MODELS.map((key) => ({ key, name: t(`about.model_${key}`), p: props.model.comparison[key][m.key] as Proportion })),
  })),
)
const f3 = (v: number) => formatFixed(v, lang.value, 3)
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-4 text-xs text-muted">
      <span v-for="key in MODELS" :key="key" class="inline-flex items-center gap-1.5">
        <span class="h-2.5 w-2.5 rounded-sm" :class="COLORS[key]" />{{ t(`about.model_${key}`) }}
      </span>
    </div>
    <div class="mt-6 grid gap-8 md:grid-cols-2">
      <div v-for="(g, gi) in groups" :key="g.label" v-reveal="gi">
        <h3 class="text-sm font-semibold text-ink">{{ g.label }}</h3>
        <div class="mt-3 space-y-2.5">
          <div v-for="(r, i) in g.rows" :key="r.key" class="grid grid-cols-[72px_1fr_44px] items-center gap-3">
            <span class="truncate text-xs" :class="r.key === 'ensemble' ? 'font-semibold text-ink' : 'text-muted'">{{ r.name }}</span>
            <div class="relative h-4 rounded bg-sand">
              <div
                class="reveal-grow h-full rounded"
                :class="COLORS[r.key]"
                :style="{ width: `${r.p.value * 100}%`, transitionDelay: `${200 + i * 120}ms` }"
              />
              <!-- 95% доверительный интервал -->
              <span
                class="absolute top-1/2 h-px -translate-y-1/2 bg-ink/70"
                :style="{ left: `${r.p.ci95[0] * 100}%`, width: `${(r.p.ci95[1] - r.p.ci95[0]) * 100}%` }"
              >
                <span class="absolute -top-1 left-0 h-2 w-px bg-ink/70" />
                <span class="absolute -top-1 right-0 h-2 w-px bg-ink/70" />
              </span>
            </div>
            <span class="text-right font-mono text-xs text-ink tabular-nums" :title="`${f3(r.p.ci95[0])}–${f3(r.p.ci95[1])}, n=${r.p.n}`">{{ f3(r.p.value) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
