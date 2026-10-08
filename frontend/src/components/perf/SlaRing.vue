<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useCountUp } from '../../composables/useCountUp'

// кольцо «доля ответов быстрее цели»: дуга дорисовывается при изменении значения
const props = defineProps<{ share: number | null; size?: number }>()
const R = 42
const C = 2 * Math.PI * R
const shown = useCountUp(toRef(props, 'share'), 900)
const offset = computed(() => C * (1 - (props.share ?? 0)))
const color = computed(() => ((props.share ?? 1) >= 0.95 ? 'var(--success)' : (props.share ?? 1) >= 0.8 ? 'var(--gold)' : 'var(--danger)'))
</script>

<template>
  <div class="relative" :style="{ width: `${size ?? 104}px`, height: `${size ?? 104}px` }">
    <svg viewBox="0 0 100 100" class="h-full w-full -rotate-90">
      <circle cx="50" cy="50" :r="R" fill="none" stroke="var(--sand)" stroke-width="9" />
      <circle
        cx="50"
        cy="50"
        :r="R"
        fill="none"
        :stroke="color"
        stroke-width="9"
        stroke-linecap="round"
        :stroke-dasharray="C"
        :stroke-dashoffset="offset"
        class="transition-[stroke-dashoffset,stroke] duration-1000 ease-(--ease-out-quint)"
      />
    </svg>
    <span class="absolute inset-0 flex items-center justify-center font-mono text-lg font-medium text-ink tabular-nums">
      {{ shown == null ? '–' : `${Math.round(shown * 100)}%` }}
    </span>
  </div>
</template>
