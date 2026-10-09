<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import {
  AcademicCapIcon,
  BookOpenIcon,
  CalendarDaysIcon,
  ChatBubbleLeftRightIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  LanguageIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'
import { useCountUp } from '../composables/useCountUp'
import { useKnowledge } from '../composables/useKnowledge'
import type { AppLocale, Level, TuitionProgram } from '../types'
import { formatNumber } from '../utils/format'
import { levelsOf, optionsOf, PLAN_YEARS, priceOf, totalOf } from '../utils/tuition'

const { t, locale } = useI18n()
const route = useRoute()
const lang = computed(() => locale.value as AppLocale)
const { catalog, loadCatalog } = useKnowledge()
const loadError = ref(false)

const query = ref('')
const programId = ref(typeof route.query.program === 'string' ? route.query.program : 'computer_engineering')
const level = ref<Level>('bachelor')
const planId = ref('')
const english = ref(false)

onMounted(() => loadCatalog().catch(() => (loadError.value = true)))

const programs = computed(() =>
  [...(catalog.value?.programs ?? [])].sort((a, b) => a.name[lang.value].localeCompare(b.name[lang.value], lang.value)),
)
const hasLevel = (p: TuitionProgram, l: Level) => !!catalog.value && levelsOf(p, catalog.value).includes(l)
const hasPhd = (p: TuitionProgram) => p.prices.some((price) => price.plan === 'phd')
const countAt = (l: Level) => programs.value.filter((p) => hasLevel(p, l)).length
// сначала уровень, затем программа: в списке только программы, у которых этот уровень есть в таблице цен
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return programs.value.filter((p) => hasLevel(p, level.value) && (!q || p.name[lang.value].toLowerCase().includes(q)))
})
const program = computed(() => catalog.value?.programs.find((p) => p.id === programId.value) ?? null)
const options = computed(() => (program.value && catalog.value ? optionsOf(program.value, level.value, catalog.value) : []))
const option = computed(() => options.value.find((o) => o.plan.id === planId.value) ?? options.value[0] ?? null)
const hasEnglish = computed(() => !!option.value?.price.english)

// программа из ссылки (?program=…) может быть только в магистратуре – тогда сразу открываем её уровень
const stopInitial = watch(catalog, () => {
  if (!catalog.value || !program.value) return
  if (!hasLevel(program.value, level.value)) level.value = levelsOf(program.value, catalog.value)[0] ?? 'bachelor'
  stopInitial()
}, { immediate: true })

// смена уровня: если у выбранной программы его нет – берём первую подходящую и мягко об этом говорим
const notice = ref<{ from: string; to: string } | null>(null)
let noticeTimer: ReturnType<typeof setTimeout> | undefined
function chooseLevel(l: Level) {
  level.value = l
  const current = program.value
  if (current && !hasLevel(current, l)) {
    const next = programs.value.find((p) => hasLevel(p, l))
    if (next) {
      notice.value = { from: current.name[lang.value], to: next.name[lang.value] }
      programId.value = next.id
      clearTimeout(noticeTimer)
      noticeTimer = setTimeout(() => (notice.value = null), 6000)
    }
  }
}
function chooseProgram(id: string) {
  programId.value = id
  notice.value = null
}
onUnmounted(() => clearTimeout(noticeTimer))
watch(options, () => {
  if (!options.value.some((o) => o.plan.id === planId.value)) planId.value = options.value[0]?.plan.id ?? ''
})
watch(hasEnglish, (has) => {
  if (!has) english.value = false
})

const price = computed(() => (option.value ? priceOf(option.value, english.value) : null))
const total = computed(() => (option.value ? totalOf(option.value, english.value) : null))
const priceShown = useCountUp(price, 650)
const totalShown = useCountUp(total, 900)
const max = computed(() => Math.max(...options.value.map((o) => priceOf(o, english.value)), 1))
const fmt = (v: number | null) => (v == null ? '–' : formatNumber(Math.round(v), lang.value, 0))
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 py-12 sm:px-6">
    <p class="eyebrow animate-rise">{{ t('calc.eyebrow') }}</p>
    <h1 class="display-title animate-rise mt-3 text-4xl sm:text-5xl" style="animation-delay: 60ms">{{ t('calc.title') }}</h1>
    <p class="animate-rise mt-4 max-w-2xl text-lg text-muted" style="animation-delay: 120ms">{{ t('calc.subtitle') }}</p>

    <p v-if="loadError" class="mt-8 text-danger">{{ t('apiErrors.network') }}</p>
    <div v-else-if="!catalog" class="mt-10 grid gap-6 lg:grid-cols-[1fr_400px]">
      <div class="card h-96 animate-pulse bg-sand/50" />
      <div class="card h-96 animate-pulse bg-sand/50" />
    </div>

    <div v-else class="mt-10 grid grid-cols-[minmax(0,1fr)] items-start gap-6 lg:grid-cols-[minmax(0,1fr)_400px]">
      <div class="space-y-6">
        <!-- 1. уровень: две крупные карточки, у каждой – сколько программ доступно -->
        <section class="card animate-rise p-5" style="animation-delay: 160ms">
          <h2 class="flex items-center gap-2 font-display font-semibold text-ink">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><AcademicCapIcon class="h-3.5 w-3.5" /></span>
            {{ t('calc.levelTitle') }}
          </h2>
          <div class="mt-4 grid gap-3 sm:grid-cols-2">
            <button
              v-for="l in (['bachelor', 'postgrad'] as Level[])"
              :key="l"
              class="group relative flex items-start gap-3.5 rounded-2xl border-2 p-4 text-left transition-all duration-300 ease-(--ease-out-quint)"
              :class="level === l ? 'border-primary bg-primary-soft/60' : 'border-line hover:-translate-y-0.5 hover:border-steel'"
              :aria-pressed="level === l"
              @click="chooseLevel(l)"
            >
              <span
                class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-colors duration-300"
                :class="level === l ? 'bg-primary text-on-primary' : 'bg-sand text-primary-strong'"
              >
                <AcademicCapIcon v-if="l === 'bachelor'" class="h-5 w-5" />
                <SparklesIcon v-else class="h-5 w-5" />
              </span>
              <span class="min-w-0">
                <span class="block font-display font-semibold text-ink">{{ t(`calc.${l}`) }}</span>
                <span class="mt-0.5 block text-xs leading-relaxed text-muted">{{ t(`calc.${l}Hint`) }}</span>
                <span class="tag mt-2">{{ t('calc.programsCount', { n: countAt(l) }) }}</span>
              </span>
              <CheckCircleIcon
                class="absolute top-3 right-3 h-5 w-5 transition-all duration-300 ease-(--ease-spring)"
                :class="level === l ? 'scale-100 text-primary' : 'scale-0'"
              />
            </button>
          </div>
        </section>

        <!-- 2. программа: только те, у которых выбранный уровень есть в таблице цен -->
        <section class="card animate-rise p-5" style="animation-delay: 220ms">
          <h2 class="flex items-center gap-2 font-display font-semibold text-ink">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><BookOpenIcon class="h-3.5 w-3.5" /></span>
            {{ t('calc.program') }}
          </h2>
          <Transition name="fade">
            <p v-if="notice" class="mt-3 flex items-start gap-2 rounded-xl bg-gold-soft px-3 py-2.5 text-sm text-ink">
              <InformationCircleIcon class="mt-0.5 h-4 w-4 shrink-0" />
              {{ t('calc.switched', notice) }}
            </p>
          </Transition>
          <label class="relative mt-4 block">
            <MagnifyingGlassIcon class="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-faint" />
            <input
              v-model="query"
              type="search"
              :placeholder="t('calc.search')"
              class="w-full rounded-xl border border-line bg-page py-2.5 pr-3 pl-9 text-[15px] text-ink outline-none transition-colors placeholder:text-faint focus:border-primary"
            />
          </label>
          <TransitionGroup tag="ul" name="msg" class="mt-3 grid max-h-72 gap-1 overflow-y-auto pr-1 sm:grid-cols-2">
            <li v-for="p in filtered" :key="p.id">
              <button
                class="flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm transition-all duration-200"
                :class="p.id === programId ? 'bg-primary text-on-primary' : 'text-muted hover:bg-sand hover:text-ink'"
                @click="chooseProgram(p.id)"
              >
                {{ p.name[lang] }}
                <span
                  v-if="level === 'postgrad' && hasPhd(p)"
                  class="shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px]"
                  :class="p.id === programId ? 'bg-white/20' : 'bg-gold-soft text-ink'"
                >PhD</span>
              </button>
            </li>
          </TransitionGroup>
          <p v-if="!filtered.length" class="px-3 py-2 text-sm text-faint">{{ t('calc.noPrograms') }}</p>
        </section>

        <!-- 3. форма обучения -->
        <section class="card animate-rise p-5" style="animation-delay: 280ms">
          <h2 class="flex items-center gap-2 font-display font-semibold text-ink">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><CalendarDaysIcon class="h-3.5 w-3.5" /></span>
            {{ t('calc.plan') }}
          </h2>
          <div class="mt-4 grid gap-2 sm:grid-cols-2">
            <button
              v-for="(o, i) in options"
              :key="o.plan.id"
              class="animate-pop flex items-start justify-between gap-3 rounded-xl border p-3.5 text-left transition-all duration-200"
              :class="o.plan.id === option?.plan.id ? 'border-primary bg-primary-soft/60' : 'border-line hover:border-steel'"
              :style="{ animationDelay: `${i * 40}ms` }"
              @click="planId = o.plan.id"
            >
              <span>
                <span class="block text-sm font-medium text-ink first-letter:uppercase">{{ o.plan.label[lang] }}</span>
                <span class="mt-0.5 block font-mono text-xs text-muted">{{ fmt(o.price.main) }} ₸</span>
              </span>
              <CheckCircleIcon class="h-5 w-5 shrink-0 transition-all duration-300" :class="o.plan.id === option?.plan.id ? 'scale-100 text-primary' : 'scale-50 text-transparent'" />
            </button>
          </div>
        </section>

        <!-- 4. отделение -->
        <section class="card animate-rise p-5" style="animation-delay: 340ms">
          <h2 class="flex items-center gap-2 font-display font-semibold text-ink">
            <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><LanguageIcon class="h-3.5 w-3.5" /></span>
            {{ t('calc.department') }}
          </h2>
          <div class="mt-4 grid w-full grid-cols-2 rounded-xl bg-sand p-1 text-sm font-semibold sm:inline-grid sm:w-auto">
            <button class="rounded-lg px-3 py-2 transition-all duration-300" :class="!english ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink'" @click="english = false">
              {{ t('calc.deptMain') }}
            </button>
            <button
              class="rounded-lg px-3 py-2 transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-40"
              :class="english ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink'"
              :disabled="!hasEnglish"
              @click="english = true"
            >
              {{ t('calc.deptEnglish') }}<span v-if="!hasEnglish" class="font-normal"> · {{ t('calc.noEnglish') }}</span>
            </button>
          </div>
        </section>
      </div>

      <!-- итог: цена «пересчитывается» при каждом выборе -->
      <aside class="animate-rise space-y-4 lg:sticky lg:top-24" style="animation-delay: 200ms">
        <div class="relative overflow-hidden rounded-3xl bg-[#0f172a] p-6 text-white dark:bg-surface dark:ring-1 dark:ring-line">
          <div class="absolute -top-12 -right-12 h-40 w-40 rounded-full border-[22px] border-[#0082c9]/40" aria-hidden="true" />
          <p class="relative font-display text-lg font-semibold">{{ program?.name[lang] }}</p>
          <p class="relative mt-1 text-sm text-white/60 first-letter:uppercase">
            {{ option?.plan.label[lang] }} · {{ english ? t('calc.deptEnglish') : t('calc.deptMain') }}
          </p>
          <p class="relative mt-6 font-display text-5xl font-extrabold tracking-tight tabular-nums">{{ fmt(priceShown) }}</p>
          <p class="relative mt-1 text-sm text-white/60">{{ t('calc.perYear') }}</p>
          <div class="relative mt-6 border-t border-white/15 pt-4">
            <p class="text-sm text-white/60">{{ t('calc.total') }}</p>
            <p v-if="total != null" class="mt-1 font-display text-2xl font-bold tabular-nums text-[#ffbb00]">
              {{ fmt(totalShown) }} <span class="text-base font-semibold text-white/60">₸</span>
            </p>
            <p v-else class="mt-1 text-sm text-white/80">{{ t('calc.unknownTerm') }}</p>
            <p v-if="total != null" class="mt-0.5 text-xs text-white/50">{{ PLAN_YEARS[option!.plan.id] }} × {{ fmt(price) }} · {{ t('calc.totalHint') }}</p>
          </div>
          <RouterLink :to="{ path: '/chat', query: { q: t('calc.discountsQuestion') } }" class="btn relative mt-6 w-full bg-[#0082c9] text-white hover:bg-[#006aa6]">
            <ChatBubbleLeftRightIcon class="h-4 w-4" />{{ t('calc.askDiscounts') }}
          </RouterLink>
        </div>

        <!-- сравнение всех форм обучения программы -->
        <div class="card p-5">
          <h3 class="text-sm font-semibold text-ink">{{ t('calc.compare') }}</h3>
          <ul class="mt-3 space-y-2.5">
            <li v-for="o in options" :key="o.plan.id">
              <button class="w-full text-left" @click="planId = o.plan.id">
                <div class="flex justify-between gap-3 text-xs">
                  <span class="truncate first-letter:uppercase" :class="o.plan.id === option?.plan.id ? 'font-semibold text-ink' : 'text-muted'">{{ o.plan.label[lang] }}</span>
                  <span class="font-mono tabular-nums text-muted">{{ fmt(priceOf(o, english)) }}</span>
                </div>
                <div class="mt-1 h-1.5 rounded-full bg-sand">
                  <div
                    class="h-full rounded-full transition-all duration-700 ease-(--ease-out-quint)"
                    :class="o.plan.id === option?.plan.id ? 'bg-primary' : 'bg-steel/50'"
                    :style="{ width: `${(priceOf(o, english) / max) * 100}%` }"
                  />
                </div>
              </button>
            </li>
          </ul>
        </div>
        <p class="px-1 text-xs leading-relaxed text-faint">{{ t('calc.sourceNote') }}</p>
      </aside>
    </div>
  </div>
</template>
