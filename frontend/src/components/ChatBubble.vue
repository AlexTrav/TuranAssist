<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowTopRightOnSquareIcon, BoltIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import type { ChatMessage } from '../composables/useChat'
import type { AppLocale, Suggestion } from '../types'
import { formatNumber, formatPercent } from '../utils/format'
import LogoMark from './icons/LogoMark.vue'

const props = defineProps<{ message: ChatMessage }>()
const emit = defineEmits<{ suggest: [suggestion: Suggestion] }>()
const { t, locale } = useI18n()

const isUser = computed(() => props.message.role === 'user')
// текст ошибки – по коду на текущем языке; неизвестный код – общий текст
const errorText = computed(() => {
  const code = props.message.error
  if (!code) return ''
  const key = `apiErrors.${code}`
  return t(key) === key ? t('apiErrors.generic') : t(key)
})
</script>

<template>
  <div class="flex gap-3" :class="isUser ? 'justify-end' : 'justify-start'">
    <LogoMark v-if="!isUser" class="mt-1 h-8 w-8 shrink-0" />
    <div class="max-w-[85%] sm:max-w-[75%]">
      <div
        class="rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm"
        :class="
          isUser
            ? 'rounded-br-md bg-brand-600 text-white'
            : message.error
              ? 'rounded-bl-md border border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300'
              : message.recognized === false
                ? 'rounded-bl-md border border-accent-200 bg-accent-100/60 text-slate-800 dark:border-accent-700/40 dark:bg-accent-700/15 dark:text-slate-100'
                : 'rounded-bl-md border border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100'
        "
      >
        <p v-if="message.error" class="flex items-start gap-2">
          <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0" />
          {{ errorText }}
        </p>
        <template v-else>
          <p v-if="!isUser && message.title" class="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-600 dark:text-brand-400">
            {{ message.title }}
          </p>
          <!-- ответы из базы содержат переводы строк и списки – сохраняем их -->
          <p class="whitespace-pre-line break-words">{{ message.text }}</p>
          <a
            v-if="message.sourceUrl"
            :href="message.sourceUrl"
            target="_blank"
            rel="noopener"
            class="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:underline dark:text-brand-400"
          >
            {{ t('chat.more') }}
            <ArrowTopRightOnSquareIcon class="h-4 w-4" />
          </a>
        </template>
      </div>

      <!-- подсказки, когда бот не уверен -->
      <div v-if="message.suggestions?.length" class="mt-2 flex flex-wrap gap-2">
        <button
          v-for="s in message.suggestions"
          :key="s.intent"
          class="rounded-full border border-brand-200 bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700 transition-colors hover:bg-brand-100 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-200 dark:hover:bg-brand-900/70"
          @click="emit('suggest', s)"
        >
          {{ s.title }}
        </button>
      </div>

      <!-- уверенность модели и время обработки – видно, что ответ получен «в реальном времени» -->
      <p
        v-if="!isUser && message.confidence !== undefined && !message.error"
        class="mt-1.5 flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500"
      >
        <BoltIcon class="h-3.5 w-3.5" />
        {{ t('chat.confidence', { value: formatPercent(message.confidence, locale as AppLocale) }) }}
        <template v-if="message.timingMs !== undefined">
          · {{ t('chat.timing', { value: formatNumber(message.timingMs, locale as AppLocale) }) }}
        </template>
      </p>
    </div>
  </div>
</template>
