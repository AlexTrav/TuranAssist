<script setup lang="ts">
import { computed } from 'vue'
import type { HistogramBucket } from '../../types'
import { bucketLabel } from '../../utils/chart'

// гистограмма задержек: столбики растут снизу; корзины медленнее цели (SLA) – жёлтые
const props = defineProps<{ buckets: HistogramBucket[]; target: number }>()

const max = computed(() => Math.max(...props.buckets.map((b) => b.count), 1))
const bars = computed(() =>
  props.buckets.map((b, i) => ({
    ...b,
    label: bucketLabel(b.le, i ? props.buckets[i - 1].le : null),
    slow: b.le == null || b.le > props.target,
  })),
)
</script>

<template>
  <div>
    <div class="flex h-40 items-end gap-1">
      <div v-for="(b, i) in bars" :key="b.label" class="group relative flex h-full flex-1 flex-col justify-end">
        <!-- подсказка с числом запросов при наведении -->
        <span class="pointer-events-none absolute -top-1 left-1/2 -translate-x-1/2 -translate-y-full rounded bg-ink px-1.5 py-0.5 font-mono text-[10px] whitespace-nowrap text-page opacity-0 transition-opacity group-hover:opacity-100">
          {{ b.count }}
        </span>
        <div
          class="origin-bottom animate-[grow-up_0.8s_var(--ease-out-quint)_both] rounded-t-md transition-[height] duration-700 ease-(--ease-out-quint)"
          :class="b.slow ? 'bg-gold' : 'bg-primary'"
          :style="{ height: `${b.count ? Math.max((b.count / max) * 100, 3) : 0}%`, animationDelay: `${i * 40}ms` }"
        />
      </div>
    </div>
    <div class="mt-1.5 flex gap-1 border-t border-line pt-1.5">
      <span v-for="b in bars" :key="b.label" class="flex-1 text-center font-mono text-[9px] text-faint sm:text-[10px]">{{ b.label }}</span>
    </div>
  </div>
</template>
