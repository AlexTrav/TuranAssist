<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { DEMO } from '../../examples'
import type { AppLocale } from '../../types'
import { formatNumber, formatPercent, formatPiece } from '../../utils/format'

// живой пример на главной: вопрос печатается, затем по шагам появляются токены и леммы,
// подслова трансформера, вероятности тем и ответ – настоящие данные модели (см. examples.ts)
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const examples = computed(() => DEMO[lang.value])

const current = ref(0)
const typed = ref('')
const phase = ref(0) // 0 – печать вопроса, 1 – токены, 2 – подслова, 3 – классификация, 4 – ответ
const leaving = ref(false)
const example = computed(() => examples.value[current.value % examples.value.length])

let timers: ReturnType<typeof setTimeout>[] = []
const later = (ms: number, fn: () => void) => timers.push(setTimeout(fn, ms))
const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function play() {
  timers.forEach(clearTimeout)
  timers = []
  leaving.value = false
  const q = example.value.question
  if (reducedMotion()) {
    typed.value = q
    phase.value = 4
    later(7000, next)
    return
  }
  typed.value = ''
  phase.value = 0
  q.split('').forEach((_, i) => later(250 + i * 38, () => (typed.value = q.slice(0, i + 1))))
  const typedAt = 250 + q.length * 38
  later(typedAt + 350, () => (phase.value = 1))
  later(typedAt + 1300, () => (phase.value = 2))
  later(typedAt + 2300, () => (phase.value = 3))
  later(typedAt + 3500, () => (phase.value = 4))
  later(typedAt + 7600, () => (leaving.value = true))
  later(typedAt + 8000, next)
}

function next() {
  current.value = (current.value + 1) % examples.value.length
  play()
}

function pick(i: number) {
  current.value = i
  play()
}

onMounted(play)
onUnmounted(() => timers.forEach(clearTimeout))
watch(lang, () => pick(0))
</script>

<template>
  <div class="card relative overflow-hidden p-0 shadow-[0_24px_60px_-28px_rgba(15,23,42,0.35)]">
    <!-- шапка карточки: подпись, язык и переключатель примеров -->
    <div class="flex items-center justify-between border-b border-line bg-sand/50 px-5 py-3">
      <span class="eyebrow">{{ t('home.demoLabel') }}</span>
      <div class="flex items-center gap-1.5">
        <button
          v-for="(_, i) in examples"
          :key="i"
          class="h-2 rounded-full transition-all duration-500 ease-(--ease-out-quint)"
          :class="i === current ? 'w-6 bg-primary' : 'w-2 bg-steel/50 hover:bg-steel'"
          :aria-label="`${i + 1}`"
          @click="pick(i)"
        />
      </div>
    </div>

    <div class="min-h-[440px] space-y-4 p-5 transition-opacity duration-300" :class="leaving ? 'opacity-0' : 'opacity-100'">
      <!-- вопрос пользователя печатается по буквам -->
      <div class="flex justify-end">
        <div class="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-[15px] text-on-primary">
          {{ typed }}<span v-if="phase === 0" class="animate-blink ml-0.5 inline-block h-4 w-0.5 translate-y-0.5 bg-on-primary" />
        </div>
      </div>

      <!-- 1. токены и леммы -->
      <div v-if="phase >= 1" class="animate-rise">
        <div class="mb-1.5 font-mono text-[11px] text-faint">tokens → lemmas</div>
        <div class="flex flex-wrap gap-1.5">
          <span
            v-for="(tok, i) in example.tokens"
            :key="tok.text + i"
            class="animate-pop rounded-md border px-2 py-0.5 font-mono text-xs"
            :class="tok.stop ? 'border-line text-faint line-through' : 'border-primary/30 bg-primary-soft text-ink'"
            :style="{ animationDelay: `${i * 70}ms` }"
          >
            {{ tok.text }}<template v-if="tok.lemma"> → <b class="font-medium text-primary-strong">{{ tok.lemma }}</b></template>
          </span>
        </div>
      </div>

      <!-- 2. подслова SentencePiece для трансформера -->
      <div v-if="phase >= 2" class="animate-rise">
        <div class="mb-1.5 font-mono text-[11px] text-faint">SentencePiece → multilingual-e5</div>
        <div class="flex flex-wrap gap-1">
          <span
            v-for="(sw, i) in example.subwords"
            :key="sw + i"
            class="animate-pop rounded bg-sand px-1.5 py-0.5 font-mono text-[11px] text-muted"
            :style="{ animationDelay: `${i * 45}ms` }"
          >{{ formatPiece(sw) }}</span>
        </div>
      </div>

      <!-- 3. вероятности тем: полосы заполняются, лучшая – цветом «Турана» -->
      <div v-if="phase >= 3" class="animate-rise space-y-1.5">
        <div class="font-mono text-[11px] text-faint">e5 × 0.8 + TF-IDF × 0.2</div>
        <div v-for="(c, i) in example.top" :key="c.title" class="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1">
          <div class="truncate text-[13px]" :class="i === 0 ? 'font-semibold text-ink' : 'text-muted'">{{ c.title }}</div>
          <div class="font-mono text-xs tabular-nums" :class="i === 0 ? 'text-primary-strong' : 'text-faint'">
            {{ formatPercent(c.p, lang, 1) }}
          </div>
          <div class="col-span-2 h-1.5 overflow-hidden rounded-full bg-sand">
            <div
              class="h-full origin-left rounded-full transition-transform duration-1000 ease-(--ease-out-quint)"
              :class="i === 0 ? 'bg-primary' : 'bg-steel/60'"
              :style="{ transform: `scaleX(${phase >= 3 ? Math.max(c.p, 0.01) : 0})`, transitionDelay: `${i * 120}ms` }"
            />
          </div>
        </div>
      </div>

      <!-- 4. ответ из базы -->
      <div v-if="phase >= 4" class="animate-rise rounded-xl border border-line bg-page p-3.5">
        <div class="text-[11px] font-semibold tracking-wide text-primary-strong uppercase">{{ example.answerTitle }}</div>
        <p class="mt-1 text-sm leading-relaxed text-ink">{{ example.answer }}</p>
        <div class="mt-2 flex gap-1.5">
          <span class="tag">{{ formatPercent(example.confidence, lang, 0) }}</span>
          <span class="tag">{{ formatNumber(example.ms, lang) }} {{ t('units.ms') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
