<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { PaperAirplaneIcon, TrashIcon } from '@heroicons/vue/24/outline'
import ChatBubble from '../components/ChatBubble.vue'
import LogoMark from '../components/icons/LogoMark.vue'
import { useChat } from '../composables/useChat'
import { EXAMPLE_QUESTIONS } from '../examples'
import type { AppLocale, Suggestion } from '../types'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { messages, pending, send, choose, clear } = useChat()

const input = ref('')
const bottom = ref<HTMLElement | null>(null)
const lang = computed(() => locale.value as AppLocale)
const examples = computed(() => EXAMPLE_QUESTIONS[lang.value])
const MAX_LENGTH = 500 // как на бэкенде

async function submit(text = input.value) {
  if (!text.trim() || pending.value) return
  input.value = ''
  await send(text)
}

function onSuggest(s: Suggestion) {
  choose(s, lang.value)
}

// Enter – отправить, Shift+Enter – перенос строки
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

// новые сообщения – прокрутка вниз
watch(
  () => [messages.value.length, pending.value],
  async () => {
    await nextTick()
    bottom.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  },
)

// переход с главной по карточке темы: /chat?q=... – сразу задаём вопрос
onMounted(() => {
  const q = route.query.q
  if (typeof q === 'string' && q.trim()) {
    router.replace({ query: {} })
    submit(q)
  } else {
    bottom.value?.scrollIntoView({ block: 'end' })
  }
})
</script>

<template>
  <div class="mx-auto flex h-[calc(100vh-4.5rem)] max-w-3xl flex-col px-4 sm:px-5">
    <div class="flex items-center justify-between py-4">
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-slate-50">{{ t('chat.title') }}</h1>
        <p class="text-sm text-slate-500 dark:text-slate-400">{{ t('chat.subtitle') }}</p>
      </div>
      <button
        v-if="messages.length"
        class="inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800"
        @click="clear"
      >
        <TrashIcon class="h-4 w-4" />
        <span class="hidden sm:inline">{{ t('chat.clear') }}</span>
      </button>
    </div>

    <div class="flex-1 space-y-4 overflow-y-auto pb-4">
      <!-- пустой чат: приветствие и примеры вопросов -->
      <div v-if="!messages.length" class="flex h-full flex-col items-center justify-center text-center">
        <LogoMark class="h-16 w-16" />
        <h2 class="mt-4 text-lg font-semibold text-slate-900 dark:text-slate-50">{{ t('chat.emptyTitle') }}</h2>
        <p class="mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">{{ t('chat.emptyText') }}</p>
        <div class="mt-6 flex flex-wrap justify-center gap-2">
          <button
            v-for="q in examples"
            :key="q"
            class="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:border-brand-300 hover:text-brand-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-brand-700"
            @click="submit(q)"
          >
            {{ q }}
          </button>
        </div>
      </div>

      <TransitionGroup name="message">
        <ChatBubble v-for="m in messages" :key="m.id" :message="m" @suggest="onSuggest" />
      </TransitionGroup>

      <!-- бот «печатает», пока ждём ответ -->
      <div v-if="pending" class="flex items-center gap-3" :aria-label="t('chat.typing')">
        <LogoMark class="h-8 w-8" />
        <div class="flex gap-1 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900">
          <span v-for="i in 3" :key="i" class="typing-dot h-2 w-2 rounded-full bg-brand-500" :style="{ animationDelay: `${i * 0.15}s` }" />
        </div>
      </div>
      <div ref="bottom" />
    </div>

    <form class="sticky bottom-0 border-t border-slate-200 bg-slate-50 py-3 dark:border-slate-800 dark:bg-slate-950" @submit.prevent="submit()">
      <div class="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white p-2 focus-within:border-brand-400 focus-within:ring-2 focus-within:ring-brand-200 dark:border-slate-700 dark:bg-slate-900 dark:focus-within:ring-brand-900">
        <textarea
          v-model="input"
          rows="1"
          :maxlength="MAX_LENGTH"
          :placeholder="t('chat.placeholder')"
          class="max-h-32 flex-1 resize-none bg-transparent px-2 py-2 text-[15px] text-slate-800 outline-none placeholder:text-slate-400 dark:text-slate-100"
          @keydown="onKeydown"
        />
        <button
          type="submit"
          :disabled="!input.trim() || pending"
          class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
          :aria-label="t('chat.send')"
        >
          <PaperAirplaneIcon class="h-5 w-5" />
        </button>
      </div>
      <p class="mt-1.5 text-center text-xs text-slate-400">{{ t('chat.hint') }}</p>
    </form>
  </div>
</template>
