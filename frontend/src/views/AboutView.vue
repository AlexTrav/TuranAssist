<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api/client'
import { LINKS } from '../links'
import type { AppLocale, GroupInfo, ModelInfo, ModelRow } from '../types'
import { formatNumber, formatProportion } from '../utils/format'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const model = ref<ModelInfo | null>(null)
const groups = ref<GroupInfo[]>([])
const loadError = ref(false)

onMounted(async () => {
  try {
    ;[model.value, groups.value] = await Promise.all([api.modelInfo(), api.intents()])
  } catch {
    loadError.value = true
  }
})

const pipeline = computed(() => [1, 2, 3, 4, 5, 6].map((n) => ({ title: t(`about.step${n}Title`), text: t(`about.step${n}Text`) })))
const rows = computed(() => {
  const c = model.value?.comparison
  if (!c) return []
  return (['tfidf', 'e5', 'ensemble'] as const).map((key) => ({ key, label: t(`about.model_${key}`), row: c[key] as ModelRow }))
})
const stack = ['Python', 'FastAPI', 'scikit-learn', 'ONNX Runtime', 'multilingual-e5-small', 'SentencePiece', 'Vue 3', 'TypeScript', 'Tailwind CSS', 'vue-i18n', 'Docker', 'GitHub Actions', 'Render', 'Hugging Face Hub', 'Telegram Bot API']
</script>

<template>
  <div class="mx-auto max-w-6xl px-5 py-12">
    <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.title') }}</h1>
    <p class="mt-3 max-w-3xl leading-relaxed text-slate-600 dark:text-slate-300">{{ t('about.intro') }}</p>

    <h2 class="mt-12 text-2xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.pipelineTitle') }}</h2>
    <ol class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <li v-for="(step, i) in pipeline" :key="i" v-reveal class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <div class="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">{{ i + 1 }}</div>
        <h3 class="mt-3 font-semibold text-slate-900 dark:text-slate-50">{{ step.title }}</h3>
        <p class="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{{ step.text }}</p>
      </li>
    </ol>

    <h2 class="mt-12 text-2xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.modelsTitle') }}</h2>
    <p class="mt-2 max-w-3xl text-sm text-slate-500 dark:text-slate-400">{{ t('about.modelsSubtitle') }}</p>
    <p v-if="loadError" class="mt-4 text-sm text-red-500">{{ t('apiErrors.network') }}</p>
    <div v-else class="mt-6 overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-800">
      <table class="w-full min-w-[720px] text-left text-sm">
        <thead class="bg-slate-100 text-slate-600 dark:bg-slate-900 dark:text-slate-300">
          <tr>
            <th class="px-4 py-3">{{ t('about.colModel') }}</th>
            <th class="px-4 py-3">{{ t('about.colTest') }}</th>
            <th class="px-4 py-3">{{ t('about.colOod') }}</th>
            <th class="px-4 py-3">{{ t('about.colExternal') }}</th>
            <th class="px-4 py-3">{{ t('about.colScenarios') }}</th>
            <th class="px-4 py-3">p50</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 bg-white dark:divide-slate-800 dark:bg-slate-950">
          <tr v-for="r in rows" :key="r.key" :class="r.key === 'ensemble' ? 'bg-brand-50/60 font-semibold dark:bg-brand-900/20' : ''">
            <td class="px-4 py-3 text-slate-900 dark:text-slate-50">{{ r.label }}</td>
            <td class="px-4 py-3 tabular-nums">{{ formatProportion(r.row.test, lang) }}</td>
            <td class="px-4 py-3 tabular-nums">{{ formatProportion(r.row.ood_rejected, lang) }}</td>
            <td class="px-4 py-3 tabular-nums">{{ formatProportion(r.row.external, lang) }}</td>
            <td class="px-4 py-3 tabular-nums">{{ formatProportion(r.row.scenarios, lang) }}</td>
            <td class="px-4 py-3 tabular-nums">{{ r.row.latency_p50_ms ? `${formatNumber(r.row.latency_p50_ms, lang)} ${t('units.ms')}` : '–' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="model" class="mt-3 text-xs text-slate-400">
      {{ t('about.modelsNote', { threshold: formatNumber(model.threshold, lang, 3), weight: formatNumber(model.weight_e5, lang, 1) }) }}
    </p>

    <h2 class="mt-12 text-2xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.topicsTitle', { n: model?.intents ?? 53 }) }}</h2>
    <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <div v-for="g in groups" :key="g.id" class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <h3 class="font-semibold text-brand-700 dark:text-brand-400">{{ g.title[lang] }}</h3>
        <ul class="mt-2 space-y-1 text-sm text-slate-600 dark:text-slate-300">
          <li v-for="i in g.intents" :key="i.id">{{ i.title[lang] }}</li>
        </ul>
      </div>
    </div>

    <h2 class="mt-12 text-2xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.stackTitle') }}</h2>
    <div class="mt-4 flex flex-wrap gap-2">
      <span v-for="s in stack" :key="s" class="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200">{{ s }}</span>
    </div>

    <h2 class="mt-12 text-2xl font-bold text-slate-900 dark:text-slate-50">{{ t('about.limitsTitle') }}</h2>
    <ul class="mt-4 list-disc space-y-2 pl-5 text-slate-600 dark:text-slate-300">
      <li v-for="n in 4" :key="n">{{ t(`about.limit${n}`) }}</li>
    </ul>

    <div class="mt-12 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <h2 class="text-lg font-semibold text-slate-900 dark:text-slate-50">{{ t('about.authorTitle') }}</h2>
      <p class="mt-2 text-slate-600 dark:text-slate-300">{{ t('about.author') }}</p>
      <div class="mt-3 flex flex-wrap gap-4 text-sm font-medium text-brand-600 dark:text-brand-400">
        <a :href="LINKS.github" target="_blank" rel="noopener" class="hover:underline">GitHub</a>
        <a :href="LINKS.telegram" target="_blank" rel="noopener" class="hover:underline">Telegram</a>
        <a :href="LINKS.huggingface" target="_blank" rel="noopener" class="hover:underline">Hugging Face</a>
      </div>
    </div>
  </div>
</template>
