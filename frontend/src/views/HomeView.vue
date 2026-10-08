<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AcademicCapIcon,
  BanknotesIcon,
  BookOpenIcon,
  BuildingLibraryIcon,
  ChatBubbleLeftRightIcon,
  CheckBadgeIcon,
  CpuChipIcon,
  GiftIcon,
  HomeModernIcon,
  PaperAirplaneIcon,
  PencilSquareIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'
import { GROUP_EXAMPLES } from '../examples'
import { LINKS } from '../links'
import type { AppLocale } from '../types'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)

const stats = computed(() => [
  { value: '53', label: t('home.statTopics') },
  { value: '3', label: t('home.statLanguages') },
  { value: '~8 ms', label: t('home.statLatency') },
])

const steps = computed(() => [
  { icon: PencilSquareIcon, title: t('home.step1Title'), text: t('home.step1Text') },
  { icon: CpuChipIcon, title: t('home.step2Title'), text: t('home.step2Text') },
  { icon: CheckBadgeIcon, title: t('home.step3Title'), text: t('home.step3Text') },
])

const groups = computed(() => [
  { id: 'admission', icon: AcademicCapIcon },
  { id: 'postgrad', icon: SparklesIcon },
  { id: 'payment', icon: BanknotesIcon },
  { id: 'grants', icon: GiftIcon },
  { id: 'study', icon: BookOpenIcon },
  { id: 'student_life', icon: HomeModernIcon },
  { id: 'about', icon: BuildingLibraryIcon },
])
</script>

<template>
  <div>
    <section class="relative overflow-hidden">
      <div class="animate-blob absolute -left-24 -top-24 h-72 w-72 rounded-full bg-brand-200/60 blur-3xl dark:bg-brand-900/40" aria-hidden="true" />
      <div class="animate-blob-delayed absolute -right-16 top-10 h-80 w-80 rounded-full bg-accent-200/50 blur-3xl dark:bg-accent-700/20" aria-hidden="true" />

      <div class="relative mx-auto max-w-6xl px-5 pb-20 pt-16 text-center sm:pt-24">
        <span class="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm font-medium text-brand-700 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-300">
          <ChatBubbleLeftRightIcon class="h-4 w-4" />
          {{ t('home.badge') }}
        </span>
        <h1 class="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl dark:text-slate-50">
          {{ t('home.title') }}
        </h1>
        <p class="mx-auto mt-5 max-w-2xl text-lg text-slate-500 dark:text-slate-400">{{ t('home.subtitle') }}</p>
        <div class="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <RouterLink
            to="/chat"
            class="w-full rounded-full bg-brand-600 px-7 py-3 text-base font-semibold text-white shadow-lg shadow-brand-600/20 transition-transform hover:scale-105 hover:bg-brand-700 sm:w-auto"
          >
            {{ t('home.ctaChat') }}
          </RouterLink>
          <a
            :href="LINKS.telegram"
            target="_blank"
            rel="noopener"
            class="inline-flex w-full items-center justify-center gap-2 rounded-full border border-slate-300 bg-white px-7 py-3 text-base font-semibold text-slate-700 transition-colors hover:border-brand-300 hover:text-brand-700 sm:w-auto dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-brand-700"
          >
            <PaperAirplaneIcon class="h-5 w-5" />
            {{ t('home.ctaTelegram') }}
          </a>
        </div>
      </div>
    </section>

    <section class="border-y border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div class="mx-auto grid max-w-6xl grid-cols-1 divide-y divide-slate-200 sm:grid-cols-3 sm:divide-x sm:divide-y-0 dark:divide-slate-800">
        <div v-for="stat in stats" :key="stat.label" v-reveal class="px-6 py-8 text-center">
          <div class="text-3xl font-bold text-brand-700 dark:text-brand-400">{{ stat.value }}</div>
          <div class="mt-1 text-sm text-slate-500 dark:text-slate-400">{{ stat.label }}</div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-6xl px-5 py-20">
      <h2 class="text-center text-3xl font-bold text-slate-900 dark:text-slate-50">{{ t('home.howTitle') }}</h2>
      <p class="mx-auto mt-3 max-w-2xl text-center text-slate-500 dark:text-slate-400">{{ t('home.howSubtitle') }}</p>
      <div class="mt-12 grid gap-6 sm:grid-cols-3">
        <div v-for="(step, i) in steps" :key="step.title" v-reveal class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
            <component :is="step.icon" class="h-6 w-6" />
          </div>
          <div class="mt-4 text-xs font-semibold uppercase tracking-wider text-accent-600">{{ t('home.stepLabel', { n: i + 1 }) }}</div>
          <h3 class="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{{ step.title }}</h3>
          <p class="mt-2 text-sm leading-relaxed text-slate-500 dark:text-slate-400">{{ step.text }}</p>
        </div>
      </div>
    </section>

    <section class="bg-white py-20 dark:bg-slate-900">
      <div class="mx-auto max-w-6xl px-5">
        <h2 class="text-center text-3xl font-bold text-slate-900 dark:text-slate-50">{{ t('home.topicsTitle') }}</h2>
        <p class="mx-auto mt-3 max-w-2xl text-center text-slate-500 dark:text-slate-400">{{ t('home.topicsSubtitle') }}</p>
        <div class="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <RouterLink
            v-for="g in groups"
            :key="g.id"
            v-reveal
            :to="{ path: '/chat', query: { q: GROUP_EXAMPLES[g.id]?.[lang] } }"
            class="group rounded-2xl border border-slate-200 p-5 transition-all hover:-translate-y-1 hover:border-brand-300 hover:shadow-lg dark:border-slate-800 dark:hover:border-brand-700"
          >
            <component :is="g.icon" class="h-7 w-7 text-brand-600 dark:text-brand-400" />
            <div class="mt-3 font-semibold text-slate-900 dark:text-slate-50">{{ t(`groups.${g.id}`) }}</div>
            <div class="mt-1 text-sm text-slate-500 group-hover:text-brand-600 dark:text-slate-400">«{{ GROUP_EXAMPLES[g.id]?.[lang] }}»</div>
          </RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>
