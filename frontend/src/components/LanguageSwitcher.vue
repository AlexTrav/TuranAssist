<script setup lang="ts">
import { computed } from 'vue'
import { useLocale } from '../composables/useLocale'

const { locale, locales } = useLocale()
const index = computed(() => locales.findIndex((l) => l.code === locale.value))
</script>

<template>
  <!-- переключатель языка: «подложка» плавно переезжает под выбранный язык -->
  <div class="relative grid grid-cols-3 rounded-xl bg-sand p-1 text-xs font-semibold" role="group" aria-label="Language">
    <span
      class="absolute inset-y-1 left-1 w-[calc((100%-0.5rem)/3)] rounded-lg bg-surface shadow-sm transition-transform duration-300 ease-(--ease-spring)"
      :style="{ transform: `translateX(${index * 100}%)` }"
      aria-hidden="true"
    />
    <button
      v-for="option in locales"
      :key="option.code"
      type="button"
      class="relative z-10 min-w-10 rounded-lg px-2 py-1.5 transition-colors"
      :class="locale === option.code ? 'text-ink' : 'text-muted hover:text-ink'"
      :aria-pressed="locale === option.code"
      @click="locale = option.code"
    >
      {{ option.label }}
    </button>
  </div>
</template>
