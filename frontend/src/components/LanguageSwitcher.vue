<script setup lang="ts">
import { useLocale } from '../composables/useLocale'

const { locale, locales } = useLocale()
</script>

<template>
  <div class="flex items-center gap-0.5 rounded-full border border-slate-300 p-0.5 text-xs font-semibold dark:border-slate-700">
    <button
      v-for="option in locales"
      :key="option.code"
      type="button"
      class="rounded-full px-2 py-1 transition-colors"
      :class="
        locale === option.code
          ? 'bg-brand-600 text-white'
          : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100'
      "
      :aria-pressed="locale === option.code"
      @click="locale = option.code"
    >
      {{ option.label }}
    </button>
  </div>
</template>
