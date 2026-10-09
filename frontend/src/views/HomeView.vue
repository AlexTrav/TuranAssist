<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  AcademicCapIcon,
  ArrowRightIcon,
  BanknotesIcon,
  BookOpenIcon,
  BuildingLibraryIcon,
  CalculatorIcon,
  ChartBarIcon,
  ChatBubbleLeftEllipsisIcon,
  CheckBadgeIcon,
  CpuChipIcon,
  FunnelIcon,
  GiftIcon,
  HomeModernIcon,
  PaperAirplaneIcon,
  RectangleStackIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'
import DemoCard from '../components/home/DemoCard.vue'
import { useCountUp } from '../composables/useCountUp'
import { GROUP_EXAMPLES } from '../examples'
import { LINKS } from '../links'
import type { AppLocale } from '../types'
import { formatNumber } from '../utils/format'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)

// цифры в первом экране «досчитываются» при загрузке
const topics = ref(0)
const languages = ref(0)
const latency = ref(0)
const topicsShown = useCountUp(topics, 1200)
const languagesShown = useCountUp(languages, 900)
const latencyShown = useCountUp(latency, 1400)
onMounted(() =>
  setTimeout(() => {
    topics.value = 53
    languages.value = 3
    latency.value = 6.5 // медиана времени ответа модели в docker-compose (см. examples.ts)
  }, 300),
)

// шаги обработки вопроса: вопрос, предобработка, классификация, ответ
const STEP_ICONS = [ChatBubbleLeftEllipsisIcon, FunnelIcon, CpuChipIcon, CheckBadgeIcon]
const steps = computed(() =>
  STEP_ICONS.map((icon, i) => ({ icon, title: t(`home.how${i + 1}Title`), text: t(`home.how${i + 1}Text`) })),
)

const groups = [
  { id: 'admission', icon: AcademicCapIcon },
  { id: 'postgrad', icon: SparklesIcon },
  { id: 'payment', icon: BanknotesIcon },
  { id: 'grants', icon: GiftIcon },
  { id: 'study', icon: BookOpenIcon },
  { id: 'student_life', icon: HomeModernIcon },
  { id: 'about', icon: BuildingLibraryIcon },
]

// мини-график для карточки «Производительность»: стилизованные столбики задержек
const bars = [38, 52, 44, 61, 35, 48, 70, 42, 55, 39, 47, 58]
</script>

<template>
  <div>
    <!-- первый экран: обещание слева, живой разбор вопроса справа -->
    <section class="relative overflow-hidden">
      <div
        class="pointer-events-none absolute inset-0 [background-image:radial-gradient(var(--line)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:radial-gradient(ellipse_at_70%_30%,black,transparent_65%)]"
        aria-hidden="true"
      />
      <div class="relative mx-auto grid max-w-7xl items-center gap-12 px-4 pt-12 pb-20 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pt-20">
        <div>
          <span class="animate-rise inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 text-sm text-muted">
            <span class="live-dot h-2 w-2 rounded-full bg-success text-success" />
            {{ t('home.eyebrow') }}
          </span>
          <h1 class="display-title animate-rise mt-6 text-[2.6rem] leading-[1.05] sm:text-6xl" style="animation-delay: 80ms">
            {{ t('home.titleStart') }}<br />
            <span class="relative inline-block text-primary">
              {{ t('home.titleAccent') }}
              <!-- жёлтая «кисточка» под акцентом рисуется при загрузке -->
              <svg class="absolute -bottom-2 left-0 h-3 w-full" viewBox="0 0 300 12" preserveAspectRatio="none" aria-hidden="true">
                <path
                  d="M2 9 C 80 2, 200 2, 298 7"
                  fill="none"
                  stroke="var(--gold)"
                  stroke-width="4"
                  stroke-linecap="round"
                  class="[stroke-dasharray:320] [stroke-dashoffset:320] [animation:draw_1s_0.6s_var(--ease-out-quint)_forwards]"
                />
              </svg>
            </span>
          </h1>
          <p class="animate-rise mt-7 max-w-xl text-lg leading-relaxed text-muted" style="animation-delay: 160ms">
            {{ t('home.subtitle') }}
          </p>
          <div class="animate-rise mt-8 flex flex-col gap-3 sm:flex-row" style="animation-delay: 240ms">
            <RouterLink to="/chat" class="btn-primary group px-6">
              {{ t('home.ctaChat') }}
              <ArrowRightIcon class="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </RouterLink>
            <a :href="LINKS.telegram" target="_blank" rel="noopener" class="btn-ghost px-6">
              <PaperAirplaneIcon class="h-4 w-4" />
              {{ t('home.ctaTelegram') }}
            </a>
          </div>
          <dl class="animate-rise mt-12 flex gap-10" style="animation-delay: 320ms">
            <div>
              <dt class="sr-only">{{ t('home.statTopics') }}</dt>
              <dd class="font-display text-3xl font-bold text-ink tabular-nums">{{ Math.round(topicsShown ?? 0) }}</dd>
              <dd class="text-sm text-muted">{{ t('home.statTopics') }}</dd>
            </div>
            <div>
              <dt class="sr-only">{{ t('home.statLanguages') }}</dt>
              <dd class="font-display text-3xl font-bold text-ink tabular-nums">{{ Math.round(languagesShown ?? 0) }}</dd>
              <dd class="text-sm text-muted">{{ t('home.statLanguages') }}</dd>
            </div>
            <div>
              <dt class="sr-only">{{ t('home.statLatency') }}</dt>
              <dd class="font-display text-3xl font-bold text-ink tabular-nums">~{{ formatNumber(latencyShown ?? 0, lang, 1) }}</dd>
              <dd class="text-sm text-muted">{{ t('home.statLatency') }}</dd>
            </div>
          </dl>
        </div>
        <div class="animate-rise lg:pl-4" style="animation-delay: 200ms">
          <DemoCard />
        </div>
      </div>
    </section>

    <!-- как это работает: четыре шага с соединяющей линией -->
    <section class="mx-auto max-w-7xl px-4 py-20 sm:px-6">
      <p v-reveal class="eyebrow">{{ t('home.howEyebrow') }}</p>
      <h2 v-reveal class="display-title mt-3 max-w-3xl text-3xl sm:text-4xl">{{ t('home.howTitle') }}</h2>
      <ol class="relative mt-12 grid gap-8 md:grid-cols-4 md:gap-6">
        <div class="absolute top-6 right-[12%] left-[12%] hidden border-t border-dashed border-steel/60 md:block" aria-hidden="true" />
        <li v-for="(step, i) in steps" :key="step.title" v-reveal="i + 1" class="relative">
          <div class="flex h-12 w-12 items-center justify-center rounded-2xl border border-line bg-surface text-primary shadow-sm">
            <component :is="step.icon" class="h-6 w-6" />
          </div>
          <h3 class="mt-5 font-display text-lg font-semibold text-ink">{{ step.title }}</h3>
          <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ step.text }}</p>
        </li>
      </ol>
    </section>

    <!-- темы: бежевая полоса, как секции на сайте университета -->
    <section class="bg-sand/70 py-20">
      <div class="mx-auto max-w-7xl px-4 sm:px-6">
        <div class="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p v-reveal class="eyebrow">{{ t('home.topicsEyebrow') }}</p>
            <h2 v-reveal class="display-title mt-3 text-3xl sm:text-4xl">{{ t('home.topicsTitle') }}</h2>
          </div>
          <p v-reveal class="max-w-sm text-muted">{{ t('home.topicsSubtitle') }}</p>
        </div>
        <div class="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <RouterLink
            v-for="(g, i) in groups"
            :key="g.id"
            v-reveal="i"
            :to="{ path: '/chat', query: { q: GROUP_EXAMPLES[g.id]?.[lang] } }"
            class="card group flex flex-col p-5 transition-all duration-300 ease-(--ease-out-quint) hover:-translate-y-1 hover:border-steel hover:shadow-[0_18px_40px_-24px_rgba(0,130,201,0.45)]"
          >
            <div class="flex items-center justify-between">
              <span class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-soft text-primary-strong transition-colors group-hover:bg-primary group-hover:text-on-primary">
                <component :is="g.icon" class="h-5 w-5" />
              </span>
              <ArrowRightIcon class="h-4 w-4 -translate-x-2 text-primary opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100" />
            </div>
            <div class="mt-4 font-display font-semibold text-ink">{{ t(`groups.${g.id}`) }}</div>
            <div class="mt-1 text-sm text-muted">«{{ GROUP_EXAMPLES[g.id]?.[lang] }}»</div>
          </RouterLink>
          <!-- восьмая карточка: все 53 темы в базе знаний -->
          <RouterLink
            v-reveal="7"
            to="/knowledge"
            class="group flex flex-col justify-between rounded-2xl border border-dashed border-steel p-5 transition-all duration-300 hover:-translate-y-1 hover:border-primary hover:bg-surface"
          >
            <span class="font-display text-4xl font-bold text-primary">53</span>
            <span class="mt-4 flex items-center gap-2 font-display font-semibold text-ink">
              {{ t('home.kbTitle') }}
              <ArrowRightIcon class="h-4 w-4 text-primary transition-transform group-hover:translate-x-1" />
            </span>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- инструменты: калькулятор, база знаний, производительность – с мини-превью -->
    <section class="mx-auto max-w-7xl px-4 py-20 sm:px-6">
      <p v-reveal class="eyebrow">{{ t('home.toolsEyebrow') }}</p>
      <h2 v-reveal class="display-title mt-3 text-3xl sm:text-4xl">{{ t('home.toolsTitle') }}</h2>
      <div class="mt-10 grid gap-5 lg:grid-cols-3">
        <RouterLink to="/calculator" v-reveal="1" class="card group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-steel">
          <div class="flex h-36 flex-col justify-center bg-primary-soft/60 px-6">
            <span class="font-mono text-xs text-muted">ВТиПО · {{ t('calc.bachelor') }}</span>
            <span class="mt-1 font-display text-3xl font-bold text-ink tabular-nums">1 476 600 <span class="text-lg text-muted">₸</span></span>
          </div>
          <div class="p-6">
            <div class="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <CalculatorIcon class="h-5 w-5 text-primary" />{{ t('home.calcTitle') }}
            </div>
            <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('home.calcText') }}</p>
          </div>
        </RouterLink>
        <RouterLink to="/knowledge" v-reveal="2" class="card group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-steel">
          <div class="flex h-36 flex-col justify-center gap-2 bg-sand px-6">
            <div v-for="w in [80, 62, 72]" :key="w" class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full bg-primary" />
              <span class="h-2 rounded-full bg-steel/40 transition-all duration-500 group-hover:bg-steel/70" :style="{ width: `${w}%` }" />
            </div>
          </div>
          <div class="p-6">
            <div class="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <RectangleStackIcon class="h-5 w-5 text-primary" />{{ t('home.kbTitle') }}
            </div>
            <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('home.kbText') }}</p>
          </div>
        </RouterLink>
        <RouterLink to="/performance" v-reveal="3" class="card group overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-steel">
          <div class="flex h-36 items-end gap-1.5 bg-[#0f172a] px-6 pb-6">
            <span
              v-for="(h, i) in bars"
              :key="i"
              class="flex-1 origin-bottom rounded-t bg-[#36baf2] transition-transform duration-500 group-hover:scale-y-110"
              :style="{ height: `${h}%`, opacity: 0.45 + (i / bars.length) * 0.55, transitionDelay: `${i * 25}ms` }"
            />
          </div>
          <div class="p-6">
            <div class="flex items-center gap-2 font-display text-lg font-semibold text-ink">
              <ChartBarIcon class="h-5 w-5 text-primary" />{{ t('home.perfTitle') }}
            </div>
            <p class="mt-2 text-[15px] leading-relaxed text-muted">{{ t('home.perfText') }}</p>
          </div>
        </RouterLink>
      </div>
    </section>

    <!-- Telegram: полоса в голубом цвете «Турана» -->
    <section class="mx-auto max-w-7xl px-4 sm:px-6">
      <div v-reveal class="relative overflow-hidden rounded-3xl bg-[#0082c9] px-8 py-12 text-white sm:px-12">
        <div class="absolute -top-16 -right-10 h-56 w-56 rounded-full border-[28px] border-white/10" aria-hidden="true" />
        <div class="absolute right-24 -bottom-20 h-40 w-40 rounded-full bg-[#ffbb00]/90" aria-hidden="true" />
        <div class="relative max-w-xl">
          <h2 class="font-display text-3xl font-bold">{{ t('home.tgTitle') }}</h2>
          <p class="mt-3 text-lg text-white/85">{{ t('home.tgText') }}</p>
          <a
            :href="LINKS.telegram"
            target="_blank"
            rel="noopener"
            class="btn mt-7 bg-white text-[#0f172a] hover:bg-white/90"
          >
            <PaperAirplaneIcon class="h-4 w-4" />
            @turan_assist_bot
          </a>
        </div>
      </div>
    </section>
  </div>
</template>

