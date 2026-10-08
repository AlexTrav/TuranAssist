<script setup lang="ts">
import { computed } from 'vue'
import type { RecentRequest } from '../types'
import { linePath, niceMax, scalePoints } from '../utils/chart'

const props = defineProps<{ points: RecentRequest[]; p95?: number | null; unit: string }>()

const W = 600
const H = 200
const top = computed(() => niceMax(Math.max(...props.points.map((p) => p.total_ms), props.p95 ?? 0, 1)))
const scaled = computed(() => scalePoints(props.points.map((p) => p.total_ms), W, H, top.value))
const path = computed(() => linePath(scaled.value))
const p95Y = computed(() => (props.p95 ? H - (Math.min(props.p95, top.value) / top.value) * H : null))
</script>

<template>
  <!-- задержка последних запросов: точки – запросы (жёлтые – «не понял»), пунктир – p95 -->
  <div class="relative">
    <svg :viewBox="`0 0 ${W} ${H}`" class="h-52 w-full overflow-visible" preserveAspectRatio="none" role="img">
      <line v-for="k in 4" :key="k" x1="0" :x2="W" :y1="(H / 4) * k" :y2="(H / 4) * k" class="stroke-slate-200 dark:stroke-slate-800" stroke-width="1" />
      <line v-if="p95Y !== null" x1="0" :x2="W" :y1="p95Y" :y2="p95Y" class="stroke-accent-500" stroke-width="1.5" stroke-dasharray="6 4" />
      <path :d="path" fill="none" class="stroke-brand-500" stroke-width="2" vector-effect="non-scaling-stroke" />
      <circle
        v-for="(pt, i) in scaled"
        :key="i"
        :cx="pt.x"
        :cy="pt.y"
        r="3"
        vector-effect="non-scaling-stroke"
        :class="points[i]?.recognized ? 'fill-brand-600' : 'fill-accent-500'"
      />
    </svg>
    <span class="absolute -top-2 left-0 text-xs text-slate-400">{{ top }} {{ unit }}</span>
    <span class="absolute -bottom-1 left-0 text-xs text-slate-400">0</span>
  </div>
</template>
