<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowsRightLeftIcon, ChatBubbleBottomCenterTextIcon, TagIcon } from '@heroicons/vue/24/outline'
import { api } from '../api/client'
import ModelBars from '../components/about/ModelBars.vue'
import { LINKS } from '../links'
import type { AppLocale, ModelInfo } from '../types'
import { formatNumber } from '../utils/format'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const model = ref<ModelInfo | null>(null)
const loadError = ref(false)

onMounted(async () => {
  try {
    model.value = await api.modelInfo()
  } catch {
    loadError.value = true
  }
})

// цифры проекта: страницы корпуса (data/corpus/manifest.json), обучающие фразы (data/phrases/train),
// автотесты бэкенда (pytest) и фронтенда (Vitest) на момент последнего коммита
const TESTS_TOTAL = 148 + 23 // pytest + Vitest
const facts = computed(() => [
  { value: '47', label: t('about.factPages') },
  { value: '1166', label: t('about.factPhrases') },
  { value: '53', label: t('home.statTopics') },
  { value: String(TESTS_TOTAL), label: t('about.factTests') },
])

const pipeline = computed(() => [1, 2, 3, 4, 5, 6].map((n) => ({ title: t(`about.step${n}Title`), text: t(`about.step${n}Text`) })))
const nlp = computed(() => [
  { icon: ChatBubbleBottomCenterTextIcon, title: t('about.nlp1Title'), text: t('about.nlp1Text') },
  { icon: TagIcon, title: t('about.nlp2Title'), text: t('about.nlp2Text') },
  { icon: ArrowsRightLeftIcon, title: t('about.nlp3Title'), text: t('about.nlp3Text') },
])
const stack = [
  'Python', 'FastAPI', 'scikit-learn', 'pymorphy3', 'ONNX Runtime', 'multilingual-e5-small', 'SentencePiece',
  'Vue 3', 'TypeScript', 'Tailwind CSS 4', 'vue-i18n', 'Vite', 'Vitest', 'pytest', 'Docker', 'GitHub Actions',
  'Render', 'GitHub Pages', 'Hugging Face Hub', 'Telegram Bot API',
]
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6">
    <p class="eyebrow animate-rise">{{ t('about.eyebrow') }}</p>
    <h1 class="display-title animate-rise mt-3 max-w-3xl text-4xl sm:text-5xl" style="animation-delay: 60ms">{{ t('about.title') }}</h1>
    <p class="animate-rise mt-5 max-w-3xl text-lg leading-relaxed text-muted" style="animation-delay: 120ms">{{ t('about.intro') }}</p>

    <dl class="mt-10 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div v-for="(f, i) in facts" :key="f.label" v-reveal="i" class="card p-5">
        <dd class="font-display text-4xl font-bold text-primary tabular-nums">{{ f.value }}</dd>
        <dt class="mt-1 text-sm text-muted">{{ f.label }}</dt>
      </div>
    </dl>

    <!-- конвейер проекта -->
    <h2 v-reveal class="display-title mt-20 text-3xl">{{ t('about.pipelineTitle') }}</h2>
    <ol class="mt-8 grid gap-x-6 gap-y-8 sm:grid-cols-2 lg:grid-cols-3">
      <li v-for="(step, i) in pipeline" :key="i" v-reveal="i % 3" class="relative border-t-2 border-line pt-5">
        <span class="absolute -top-0.5 left-0 h-0.5 w-12 bg-primary" />
        <span class="font-mono text-xs text-primary-strong">0{{ i + 1 }}</span>
        <h3 class="mt-2 font-display text-lg font-semibold text-ink">{{ step.title }}</h3>
        <p class="mt-1.5 text-[15px] leading-relaxed text-muted">{{ step.text }}</p>
      </li>
    </ol>

    <!-- три NLP-компонента -->
    <section class="mt-20 rounded-3xl bg-sand/70 p-6 sm:p-10">
      <h2 v-reveal class="display-title text-3xl">{{ t('about.nlpTitle') }}</h2>
      <div class="mt-8 grid gap-5 md:grid-cols-3">
        <div v-for="(c, i) in nlp" :key="c.title" v-reveal="i" class="card p-6">
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-on-primary">
            <component :is="c.icon" class="h-5 w-5" />
          </span>
          <h3 class="mt-4 font-display text-lg font-semibold text-ink">{{ c.title }}</h3>
          <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ c.text }}</p>
        </div>
      </div>
    </section>

    <!-- сравнение моделей -->
    <h2 v-reveal class="display-title mt-20 text-3xl">{{ t('about.modelsTitle') }}</h2>
    <p v-reveal class="mt-3 max-w-3xl text-muted">{{ t('about.modelsSubtitle') }}</p>
    <p v-if="loadError" class="mt-6 text-danger">{{ t('apiErrors.network') }}</p>
    <div v-else-if="model" class="card mt-8 p-6 sm:p-8">
      <ModelBars :model="model" />
      <p class="mt-8 font-mono text-xs text-faint">
        {{ t('about.modelsNote', { threshold: formatNumber(model.threshold, lang, 3), weight: formatNumber(model.weight_e5, lang, 1) }) }}
      </p>
    </div>
    <div v-else class="card mt-8 h-72 animate-pulse bg-sand/50" />

    <div class="mt-20 grid gap-10 lg:grid-cols-2">
      <section v-reveal>
        <h2 class="display-title text-2xl">{{ t('about.stackTitle') }}</h2>
        <div class="mt-5 flex flex-wrap gap-2">
          <span v-for="(s, i) in stack" :key="s" class="chip animate-pop cursor-default" :style="{ animationDelay: `${i * 30}ms` }">{{ s }}</span>
        </div>
      </section>
      <section v-reveal="1">
        <h2 class="display-title text-2xl">{{ t('about.limitsTitle') }}</h2>
        <ul class="mt-5 space-y-3">
          <li v-for="n in 4" :key="n" class="flex gap-3 text-[15px] leading-relaxed text-muted">
            <span class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-gold" />{{ t(`about.limit${n}`) }}
          </li>
        </ul>
      </section>
    </div>

    <section v-reveal class="card mt-20 flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
      <div>
        <h2 class="font-display text-lg font-semibold text-ink">{{ t('about.authorTitle') }}</h2>
        <p class="mt-1 text-muted">{{ t('about.author') }}</p>
      </div>
      <div class="flex shrink-0 flex-wrap gap-2">
        <a :href="LINKS.github" target="_blank" rel="noopener" class="btn-ghost !px-4 !py-2 text-sm">GitHub ↗</a>
        <a :href="LINKS.telegram" target="_blank" rel="noopener" class="btn-ghost !px-4 !py-2 text-sm">Telegram ↗</a>
        <a :href="LINKS.huggingface" target="_blank" rel="noopener" class="btn-ghost !px-4 !py-2 text-sm">Hugging Face ↗</a>
      </div>
    </section>
  </div>
</template>
