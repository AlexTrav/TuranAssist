<script setup lang="ts">
import { computed } from 'vue'
import type { RecentRequest } from '../types'
import { areaPath, linePath, niceMax, scalePoints } from '../utils/chart'

// задержка последних запросов: линия с заливкой, точки-запросы (жёлтые – «не понял», серо-голубые – уточнение темы), пунктир – p95.
// точки привязаны к времени запроса: новые появляются справа, старые плавно уезжают влево
const props = defineProps<{ points: RecentRequest[]; p95?: number | null; unit: string }>()

const W = 600
const H = 220
const top = computed(() => niceMax(Math.max(...props.points.map((p) => p.total_ms), props.p95 ?? 0, 1)))
const scaled = computed(() => scalePoints(props.points.map((p) => p.total_ms), W, H, top.value))
const line = computed(() => linePath(scaled.value))
const area = computed(() => areaPath(scaled.value, H))
const y = (v: number) => H - (Math.min(v, top.value) / top.value) * H
const p95Y = computed(() => (props.p95 ? y(props.p95) : null))
const grid = computed(() => [0.25, 0.5, 0.75, 1].map((k) => ({ y: H - H * k, label: Math.round(top.value * k) })))
</script>

<template>
  <div class="relative pl-9">
    <svg :viewBox="`0 0 ${W} ${H}`" class="h-56 w-full overflow-visible" preserveAspectRatio="none" role="img">
      <defs>
        <linearGradient id="latency-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="var(--primary)" stop-opacity="0.28" />
          <stop offset="1" stop-color="var(--primary)" stop-opacity="0" />
        </linearGradient>
      </defs>
      <line v-for="g in grid" :key="g.y" x1="0" :x2="W" :y1="g.y" :y2="g.y" stroke="var(--line)" stroke-width="1" vector-effect="non-scaling-stroke" />
      <path :d="area" fill="url(#latency-fill)" class="transition-all duration-700" />
      <path :d="line" fill="none" stroke="var(--primary)" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round" />
      <line
        v-if="p95Y !== null"
        x1="0"
        :x2="W"
        :y1="p95Y"
        :y2="p95Y"
        stroke="var(--gold)"
        stroke-width="1.5"
        stroke-dasharray="6 5"
        vector-effect="non-scaling-stroke"
        class="transition-all duration-700"
      />
    </svg>
    <!-- точки – HTML поверх SVG: в SVG с preserveAspectRatio=none круги растягивались бы в эллипсы -->
    <div class="pointer-events-none absolute inset-y-0 right-0 left-9">
      <span
        v-for="(pt, i) in scaled"
        :key="points[i].ts"
        class="absolute h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-surface transition-all duration-700 ease-(--ease-out-quint)"
        :class="points[i].recognized ? 'bg-primary' : points[i].rule === 'clarify' ? 'bg-steel' : 'bg-gold'"
        :style="{ left: `${(pt.x / W) * 100}%`, top: `${(pt.y / H) * 100}%` }"
      />
    </div>
    <span v-for="g in grid" :key="g.label" class="absolute left-0 -translate-y-1/2 font-mono text-[10px] text-faint" :style="{ top: `${(g.y / H) * 100}%` }">
      {{ g.label }}
    </span>
    <span class="absolute bottom-0 left-0 translate-y-1/2 font-mono text-[10px] text-faint">0 {{ unit }}</span>
  </div>
</template>
