<script setup lang="ts">
import type { Component } from 'vue'

// карточка метрики: подпись, крупное число моноширинным шрифтом (как телеметрия), пояснение
defineProps<{ label: string; value: string; hint?: string; icon?: Component; accent?: boolean; unit?: string }>()
</script>

<template>
  <div class="card group relative overflow-hidden p-5 transition-colors hover:border-steel">
    <div class="flex items-center gap-2 text-sm font-medium text-muted">
      <component :is="icon" v-if="icon" class="h-4 w-4 text-primary" />
      {{ label }}
    </div>
    <div class="mt-3 flex items-baseline gap-1.5">
      <span class="font-mono text-3xl font-medium tracking-tight tabular-nums" :class="accent ? 'text-primary-strong' : 'text-ink'">{{ value }}</span>
      <span v-if="unit" class="text-sm text-muted">{{ unit }}</span>
    </div>
    <div v-if="hint" class="mt-1 text-xs text-faint">{{ hint }}</div>
    <slot />
  </div>
</template>
