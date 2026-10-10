<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AppLocale } from '../../types'
import { formatPercent } from '../../utils/format'

// как бот ответил на вопросы с запуска сервера: модель выше порога, цена программы (сумма интентов
// стоимости или программа + слова о цене), умный поиск, уточнение темы и «не понял»
const props = defineProps<{ rules: Record<string, number> | null; context: number }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)

const GROUPS = [
  { key: 'model', rules: ['model'], color: 'bg-primary' },
  { key: 'price', rules: ['tuition_sum', 'program'], color: 'bg-primary-strong' },
  { key: 'search', rules: ['search'], color: 'bg-success' },
  { key: 'clarify', rules: ['clarify'], color: 'bg-steel' },
  { key: 'fallback', rules: ['fallback'], color: 'bg-gold' },
]

const total = computed(() => Object.values(props.rules ?? {}).reduce((a, b) => a + b, 0))
const parts = computed(() =>
  GROUPS.map((g) => {
    const n = g.rules.reduce((sum, r) => sum + (props.rules?.[r] ?? 0), 0)
    return { ...g, n, share: total.value ? n / total.value : 0 }
  }),
)
</script>

<template>
  <div class="card p-5 sm:p-6">
    <div class="flex flex-wrap items-baseline justify-between gap-2">
      <h2 class="font-display font-semibold text-ink">{{ t('performance.rulesTitle') }}</h2>
      <span class="text-xs text-faint">{{ t('performance.rulesHint', { n: total }) }}</span>
    </div>
    <template v-if="total">
      <div class="mt-4 flex h-3 overflow-hidden rounded-full bg-sand">
        <div
          v-for="p in parts"
          :key="p.key"
          :class="p.color"
          class="h-full transition-all duration-700 ease-(--ease-out-quint)"
          :style="{ width: `${p.share * 100}%` }"
        />
      </div>
      <ul class="mt-5 grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3 lg:grid-cols-5">
        <li v-for="p in parts" :key="p.key">
          <span class="flex items-center gap-1.5 text-sm font-medium text-ink">
            <span class="h-2 w-2 shrink-0 rounded-full" :class="p.color" />{{ t(`performance.rule_${p.key}`) }}
          </span>
          <span class="mt-1 block font-mono text-lg text-ink tabular-nums">
            {{ p.n }}<span class="ml-1.5 text-xs text-faint">{{ formatPercent(p.share, lang) }}</span>
          </span>
          <span class="block text-xs text-faint">{{ t(`performance.rule_${p.key}Hint`) }}</span>
        </li>
      </ul>
      <p class="mt-4 font-mono text-[11px] text-faint">{{ t('performance.rulesContext', { n: context }) }}</p>
    </template>
    <p v-else class="mt-4 text-sm text-faint">{{ t('performance.rulesEmpty') }}</p>
  </div>
</template>
