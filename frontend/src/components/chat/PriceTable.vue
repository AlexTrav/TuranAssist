<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRightIcon } from '@heroicons/vue/24/outline'
import type { AppLocale, PriceCard } from '../../types'
import { formatNumber } from '../../utils/format'

// цены программы по формам обучения: таблица вместо сплошного текста, переход в калькулятор
const props = defineProps<{ card: PriceCard }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const hasEnglish = computed(() => props.card.rows.some((r) => r.english))
const max = computed(() => Math.max(...props.card.rows.map((r) => r.english ?? r.main)))
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-line">
    <div class="flex flex-col gap-0.5 bg-sand/60 px-3.5 py-2.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-3">
      <span class="font-display text-sm font-semibold text-ink">{{ card.name }}</span>
      <span class="text-[11px] text-faint sm:shrink-0">{{ t('price.perYear') }}</span>
    </div>
    <table class="w-full text-sm">
      <thead class="sr-only">
        <tr>
          <th>{{ t('price.plan') }}</th>
          <th>{{ t('price.main') }}</th>
          <th v-if="hasEnglish">{{ t('price.english') }}</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-line">
        <tr v-for="(row, i) in card.rows" :key="row.plan" class="animate-rise" :style="{ animationDelay: `${i * 50}ms` }">
          <td class="py-2 pr-2 pl-3.5 text-muted">
            {{ row.label }}
            <!-- полоса пропорциональна цене – дорогие и дешёвые формы видны сразу -->
            <div class="mt-1 h-1 rounded-full bg-sand">
              <div class="h-full rounded-full bg-primary/70" :style="{ width: `${(row.main / max) * 100}%` }" />
            </div>
          </td>
          <td class="py-2 pr-3.5 text-right align-top font-mono text-[13px] font-medium whitespace-nowrap text-ink tabular-nums">
            {{ formatNumber(row.main, lang, 0) }} ₸
            <div v-if="row.english" class="text-[11px] font-normal text-faint">EN {{ formatNumber(row.english, lang, 0) }} ₸</div>
          </td>
        </tr>
      </tbody>
    </table>
    <RouterLink
      :to="{ path: '/calculator', query: { program: card.program } }"
      class="group flex items-center justify-end gap-1 border-t border-line px-3.5 py-2 text-xs font-semibold text-primary-strong hover:bg-primary-soft/50"
    >
      {{ t('price.openCalculator') }}
      <ArrowRightIcon class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
    </RouterLink>
  </div>
</template>
