<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{ label: string; value: string; hint?: string; icon?: Component; accent?: boolean }>()
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
    <div class="flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400">
      <component :is="icon" v-if="icon" class="h-5 w-5 text-brand-500" />
      {{ label }}
    </div>
    <div
      class="mt-2 text-3xl font-bold tabular-nums"
      :class="accent ? 'text-brand-600 dark:text-brand-400' : 'text-slate-900 dark:text-slate-50'"
    >
      {{ value }}
    </div>
    <div v-if="hint" class="mt-1 text-xs text-slate-400 dark:text-slate-500">{{ hint }}</div>
    <slot />
  </div>
</template>
