<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowTopRightOnSquareIcon,
  BeakerIcon,
  CheckIcon,
  ClipboardDocumentIcon,
  ExclamationTriangleIcon,
  HandThumbDownIcon,
  HandThumbUpIcon,
  QuestionMarkCircleIcon,
} from '@heroicons/vue/24/outline'
import { HandThumbDownIcon as ThumbDownSolid, HandThumbUpIcon as ThumbUpSolid } from '@heroicons/vue/24/solid'
import type { ChatMessage } from '../composables/useChat'
import { useKnowledge } from '../composables/useKnowledge'
import type { AppLocale } from '../types'
import { formatNumber, formatPercent } from '../utils/format'
import ExplainPanel from './chat/ExplainPanel.vue'
import PriceTable from './chat/PriceTable.vue'
import RichText from './chat/RichText.vue'
import LogoMark from './icons/LogoMark.vue'

// last – последний ответ в ленте: только под ним показываются «Также спрашивают»
const props = defineProps<{ message: ChatMessage; last?: boolean }>()
const emit = defineEmits<{ suggest: [suggestion: { intent: string; title: string }]; rate: [useful: boolean] }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const { related } = useKnowledge()

const isUser = computed(() => props.message.role === 'user')
const explainOpen = ref(false)
const copied = ref(false)

// текст ошибки – по коду на текущем языке; неизвестный код – общий текст
const errorText = computed(() => {
  const code = props.message.error
  if (!code) return ''
  const key = `apiErrors.${code}`
  return t(key) === key ? t('apiErrors.generic') : t(key)
})
const relatedTopics = computed(() =>
  props.last && props.message.recognized && props.message.intent ? related(props.message.intent).map((i) => ({ intent: i.id, title: i.title[lang.value] })) : [],
)
const programNames = computed(() => props.message.prices?.map((p) => p.name) ?? [])

async function copy() {
  try {
    await navigator.clipboard.writeText(props.message.text)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    // буфер обмена недоступен (http без TLS, запрет браузера) – молча пропускаем
  }
}
</script>

<template>
  <!-- вопрос пользователя -->
  <div v-if="isUser" class="flex justify-end">
    <div class="max-w-[85%] rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-[15px] leading-relaxed break-words whitespace-pre-line text-on-primary sm:max-w-[70%]">
      {{ message.text }}
    </div>
  </div>

  <!-- ответ бота -->
  <div v-else class="flex gap-3">
    <LogoMark class="mt-0.5 h-8 w-8 shrink-0" />
    <div class="min-w-0 flex-1 sm:max-w-[85%]">
      <div
        class="rounded-2xl rounded-tl-md border px-4 py-3.5"
        :class="
          message.error
            ? 'border-danger/30 bg-danger-soft text-danger'
            : message.recognized === false
              ? 'border-gold/50 bg-gold-soft/60'
              : 'border-line bg-surface'
        "
      >
        <p v-if="message.error" class="flex items-start gap-2 text-[15px]">
          <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0" />
          {{ errorText }}
        </p>
        <template v-else>
          <p v-if="message.recognized === false" class="mb-1.5 flex items-center gap-1.5 text-xs font-semibold tracking-wide text-ink/70 uppercase">
            <QuestionMarkCircleIcon class="h-4 w-4" />{{ message.clarify ? t('chat.clarifyTitle') : t('chat.notUnderstood') }}
          </p>
          <p v-else-if="message.title" class="mb-1.5 text-xs font-semibold tracking-wide text-primary-strong uppercase">
            {{ message.title }}
          </p>

          <!-- цены программы – таблицей; общий текст ответа не дублируем -->
          <div v-if="message.prices?.length" class="space-y-3">
            <PriceTable v-for="card in message.prices" :key="card.program" :card="card" />
          </div>
          <RichText v-else :text="message.text" class="text-ink" />

          <!-- подсказки, когда бот не уверен -->
          <div v-if="message.suggestions?.length" class="mt-3">
            <p class="text-sm text-muted">{{ message.clarify ? t('chat.clarifyPick') : t('chat.maybeMeant') }}</p>
            <div class="mt-2 flex flex-wrap gap-2">
              <button
                v-for="(s, i) in message.suggestions"
                :key="s.intent"
                class="chip animate-pop"
                :style="{ animationDelay: `${150 + i * 70}ms` }"
                @click="emit('suggest', s)"
              >
                {{ s.title }}
                <span class="font-mono text-[11px] text-faint">{{ formatPercent(s.confidence, lang) }}</span>
              </button>
            </div>
          </div>

          <a
            v-if="message.sourceUrl"
            :href="message.sourceUrl"
            target="_blank"
            rel="noopener"
            class="link mt-3 inline-flex items-center gap-1.5 text-sm no-underline"
          >
            {{ t('chat.more') }}
            <ArrowTopRightOnSquareIcon class="h-4 w-4" />
          </a>
        </template>
      </div>

      <!-- телеметрия и действия: уверенность, время, разбор, копирование, оценка -->
      <div v-if="!message.error" class="mt-1.5 flex flex-wrap items-center gap-x-1.5 gap-y-1 pl-1">
        <span v-if="message.confidence !== undefined" class="tag">{{ t('chat.confidence', { value: formatPercent(message.confidence, lang) }) }}</span>
        <span v-if="message.timingMs !== undefined" class="tag">{{ t('chat.timing', { value: formatNumber(message.timingMs, lang) }) }}</span>
        <span v-if="message.contextUsed" class="tag !bg-gold-soft !text-ink">↩ {{ t('chat.followUp') }}</span>

        <span class="ml-auto flex items-center gap-0.5">
          <button
            v-if="message.explain"
            class="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium transition-colors"
            :class="explainOpen ? 'bg-primary-soft text-primary-strong' : 'text-muted hover:bg-sand hover:text-ink'"
            :aria-expanded="explainOpen"
            @click="explainOpen = !explainOpen"
          >
            <BeakerIcon class="h-4 w-4" />
            <span class="hidden sm:inline">{{ explainOpen ? t('chat.explainHide') : t('chat.explainShow') }}</span>
          </button>
          <button class="rounded-lg p-1.5 text-muted transition-colors hover:bg-sand hover:text-ink" :aria-label="t('common.copy')" :title="copied ? t('common.copied') : t('common.copy')" @click="copy">
            <CheckIcon v-if="copied" class="animate-pop h-4 w-4 text-success" />
            <ClipboardDocumentIcon v-else class="h-4 w-4" />
          </button>
          <button
            class="rounded-lg p-1.5 transition-colors hover:bg-sand disabled:hover:bg-transparent"
            :class="message.feedback === 'up' ? 'text-success' : 'text-muted hover:text-ink'"
            :disabled="!!message.feedback"
            :aria-label="t('chat.useful')"
            :title="t('chat.useful')"
            @click="emit('rate', true)"
          >
            <ThumbUpSolid v-if="message.feedback === 'up'" class="animate-pop h-4 w-4" />
            <HandThumbUpIcon v-else class="h-4 w-4" />
          </button>
          <button
            class="rounded-lg p-1.5 transition-colors hover:bg-sand disabled:hover:bg-transparent"
            :class="message.feedback === 'down' ? 'text-danger' : 'text-muted hover:text-ink'"
            :disabled="!!message.feedback"
            :aria-label="t('chat.notUseful')"
            :title="t('chat.notUseful')"
            @click="emit('rate', false)"
          >
            <ThumbDownSolid v-if="message.feedback === 'down'" class="animate-pop h-4 w-4" />
            <HandThumbDownIcon v-else class="h-4 w-4" />
          </button>
        </span>
      </div>
      <p v-if="message.feedback" class="animate-rise mt-1 pl-1 text-right text-xs text-faint">{{ t('chat.thanks') }}</p>

      <!-- панель «Как бот понял вопрос» раскрывается на всю высоту содержимого -->
      <div v-if="message.explain" class="expand" :data-open="explainOpen">
        <div>
          <div class="mt-2 rounded-2xl border border-line bg-surface p-4">
            <ExplainPanel v-if="explainOpen" :explain="message.explain" :program-names="programNames" />
          </div>
        </div>
      </div>

      <!-- «Также спрашивают»: соседние темы той же группы -->
      <div v-if="relatedTopics.length" class="mt-3">
        <p class="mb-1.5 pl-1 text-xs font-medium text-faint">{{ t('chat.related') }}</p>
        <div class="flex flex-wrap gap-1.5">
          <button v-for="r in relatedTopics" :key="r.intent" class="chip !py-1 text-[13px]" @click="emit('suggest', r)">{{ r.title }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
