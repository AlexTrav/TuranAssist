<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CpuChipIcon, LanguageIcon, PuzzlePieceIcon, ScissorsIcon } from '@heroicons/vue/24/outline'
import { useKnowledge } from '../../composables/useKnowledge'
import type { AppLocale, Explain } from '../../types'
import { formatNumber, formatPercent, formatPiece } from '../../utils/format'

// разбор вопроса по ступеням конвейера: язык -> токены и леммы -> подслова -> классификация -> решение
const props = defineProps<{ explain: Explain; programNames: string[] }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const { titleOf } = useKnowledge()

const TUITION = ['tuition_bachelor', 'tuition_postgrad']
// уверенность, по которой принято решение: её присылает сервер (для «программы» – сумма двух тем стоимости,
// для уточнения – сумма предложенных тем); у старых сообщений из истории её нет – считаем сами
const decisive = computed(() => {
  if (props.explain.decisive != null) return props.explain.decisive
  const top = props.explain.top
  if (props.explain.rule === 'tuition_sum') return top.filter((c) => TUITION.includes(c.intent)).reduce((s, c) => s + c.probability, 0)
  return top[0]?.probability ?? 0
})
const RULE_KEYS: Record<Explain['rule'], string> = {
  model: 'explain.ruleModel',
  tuition_sum: 'explain.ruleTuition',
  program: 'explain.ruleProgram',
  clarify: 'explain.ruleClarify',
  chosen: 'explain.ruleChosen',
  fallback: 'explain.ruleFallback',
}
const ruleText = computed(() => t(RULE_KEYS[props.explain.rule] ?? 'explain.ruleFallback', { p: formatPercent(decisive.value, lang.value, 1) }))
const pct = (v: number) => formatPercent(v, lang.value, 1)
</script>

<template>
  <ol class="relative space-y-5 pl-8">
    <!-- вертикальная линия конвейера -->
    <span class="absolute top-2 bottom-2 left-[11px] w-px bg-line" aria-hidden="true" />

    <li class="animate-rise relative">
      <span class="absolute top-0 -left-8 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><LanguageIcon class="h-3.5 w-3.5" /></span>
      <h4 class="text-sm font-semibold text-ink">{{ t('explain.step1') }}</h4>
      <div class="mt-1.5 flex flex-wrap items-center gap-2">
        <span class="tag !bg-primary-soft !text-primary-strong">{{ explain.language }} · {{ t(`langs.${explain.language}`) }}</span>
        <code class="font-mono text-xs text-muted">«{{ explain.normalized }}»</code>
      </div>
      <p class="mt-1 text-xs text-faint">{{ t('explain.step1Hint') }}</p>
    </li>

    <li class="animate-rise relative" style="animation-delay: 80ms">
      <span class="absolute top-0 -left-8 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><ScissorsIcon class="h-3.5 w-3.5" /></span>
      <h4 class="text-sm font-semibold text-ink">{{ t('explain.step2') }}</h4>
      <div class="mt-1.5 flex flex-wrap gap-1.5">
        <span
          v-for="(tok, i) in explain.tokens"
          :key="i"
          class="animate-pop rounded-md border px-2 py-0.5 font-mono text-xs"
          :class="tok.stopword ? 'border-line text-faint line-through' : 'border-primary/30 bg-primary-soft text-ink'"
          :style="{ animationDelay: `${120 + i * 40}ms` }"
        >
          {{ tok.text }}<template v-if="tok.lemma !== tok.text"> → <b class="font-medium text-primary-strong">{{ tok.lemma }}</b></template>
        </span>
      </div>
      <p class="mt-1 text-xs text-faint">{{ t('explain.step2Hint') }}</p>
    </li>

    <li class="animate-rise relative" style="animation-delay: 160ms">
      <span class="absolute top-0 -left-8 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><PuzzlePieceIcon class="h-3.5 w-3.5" /></span>
      <h4 class="text-sm font-semibold text-ink">{{ t('explain.step3') }}</h4>
      <div class="mt-1.5 flex flex-wrap gap-1">
        <span
          v-for="(sw, i) in explain.subwords"
          :key="i"
          class="animate-pop rounded bg-sand px-1.5 py-0.5 font-mono text-[11px] text-muted"
          :style="{ animationDelay: `${200 + i * 25}ms` }"
        >{{ formatPiece(sw) }}</span>
        <span v-if="explain.subwords_total > explain.subwords.length" class="px-1 font-mono text-[11px] text-faint">…</span>
      </div>
      <p class="mt-1 text-xs text-faint">{{ t('explain.step3Hint', { n: explain.subwords_total }) }}</p>
    </li>

    <li class="animate-rise relative" style="animation-delay: 240ms">
      <span class="absolute top-0 -left-8 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-on-primary"><CpuChipIcon class="h-3.5 w-3.5" /></span>
      <h4 class="text-sm font-semibold text-ink">{{ t('explain.step4') }}</h4>
      <p v-if="explain.context_used" class="mt-1.5 rounded-lg bg-gold-soft px-2.5 py-1.5 text-xs text-ink">
        {{ t('explain.context') }} <span class="font-mono">«{{ explain.classified_text }}»</span>
      </p>
      <div class="mt-2 space-y-2.5">
        <div v-for="(c, i) in explain.top" :key="c.intent">
          <div class="flex items-baseline justify-between gap-3 text-[13px]">
            <span class="truncate" :class="i === 0 ? 'font-semibold text-ink' : 'text-muted'">{{ titleOf(c.intent, lang) }}</span>
            <span class="font-mono text-xs tabular-nums" :class="i === 0 ? 'text-primary-strong' : 'text-faint'">{{ pct(c.probability) }}</span>
          </div>
          <!-- полоса вероятности ансамбля; черта – порог уверенности -->
          <div class="relative mt-1 h-2 rounded-full bg-sand">
            <div
              class="h-full origin-left animate-[grow_0.9s_var(--ease-out-quint)_both] rounded-full"
              :class="i === 0 ? 'bg-primary' : 'bg-steel/60'"
              :style="{ width: `${Math.max(c.probability * 100, 0.8)}%`, animationDelay: `${300 + i * 90}ms` }"
            />
            <span class="absolute -top-1 -bottom-1 w-0.5 rounded bg-gold" :style="{ left: `${explain.threshold * 100}%` }" aria-hidden="true" />
          </div>
          <div class="mt-0.5 font-mono text-[10px] text-faint">e5 {{ pct(c.e5) }} · TF-IDF {{ pct(c.tfidf) }}</div>
        </div>
      </div>
      <p class="mt-2 text-xs text-faint">
        {{ t('explain.step4Hint', { e5: formatNumber(explain.weights.e5, lang, 1), tfidf: formatNumber(explain.weights.tfidf, lang, 1), threshold: pct(explain.threshold) }) }}
      </p>
      <div v-if="programNames.length" class="mt-2 flex flex-wrap items-center gap-1.5 text-xs">
        <span class="text-muted">{{ t('explain.entities') }}:</span>
        <span v-for="name in programNames" :key="name" class="tag !bg-gold-soft !text-ink">{{ name }}</span>
      </div>
      <p
        class="mt-2.5 rounded-lg border px-3 py-2 text-[13px]"
        :class="explain.rule === 'fallback' || explain.rule === 'clarify' ? 'border-gold/50 bg-gold-soft text-ink' : 'border-primary/30 bg-primary-soft text-ink'"
      >
        {{ ruleText }}
      </p>
    </li>
  </ol>
</template>
