<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowUpIcon, ListBulletIcon, PlusIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import ChatBubble from '../components/ChatBubble.vue'
import TopicsPanel from '../components/chat/TopicsPanel.vue'
import LogoMark from '../components/icons/LogoMark.vue'
import { useChat } from '../composables/useChat'
import { useKnowledge } from '../composables/useKnowledge'
import { EXAMPLE_QUESTIONS } from '../examples'
import type { AppLocale } from '../types'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { messages, pending, send, choose, rate, clear } = useChat()
const { loadGroups } = useKnowledge()

const input = ref('')
const textarea = ref<HTMLTextAreaElement | null>(null)
const scroller = ref<HTMLElement | null>(null)
const topicsOpen = ref(false) // выезжающая панель тем на телефоне
const lang = computed(() => locale.value as AppLocale)
const examples = computed(() => EXAMPLE_QUESTIONS[lang.value])
const MAX_LENGTH = 500 // как на бэкенде
const lastBotId = computed(() => [...messages.value].reverse().find((m) => m.role === 'bot')?.id)

async function submit(text = input.value) {
  if (!text.trim() || pending.value) return
  input.value = ''
  await nextTick()
  resize()
  await send(text)
}

function pickTopic(topic: { intent: string; title: string }) {
  topicsOpen.value = false
  choose(topic, lang.value)
}

// Enter – отправить, Shift+Enter – перенос строки
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

// поле ввода растёт вместе с текстом до шести строк
function resize() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 168)}px`
}

function scrollDown(smooth = true) {
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: smooth ? 'smooth' : 'auto' })
}

// новые сообщения – прокрутка вниз
watch(
  () => [messages.value.length, pending.value],
  async () => {
    await nextTick()
    scrollDown()
  },
)

// переход с главной по карточке темы: /chat?q=... – сразу задаём вопрос
onMounted(() => {
  loadGroups().catch(() => {}) // темы для боковой панели и «Также спрашивают»; без них чат работает
  const q = route.query.q
  if (typeof q === 'string' && q.trim()) {
    router.replace({ query: {} })
    submit(q)
  } else {
    nextTick(() => scrollDown(false))
  }
  textarea.value?.focus({ preventScroll: true })
})
</script>

<template>
  <div class="mx-auto grid h-[calc(100dvh-4rem)] max-w-7xl grid-cols-[minmax(0,1fr)] lg:grid-cols-[280px_minmax(0,1fr)]">
    <!-- темы: боковая панель на компьютере -->
    <aside class="hidden overflow-y-auto border-r border-line px-4 py-5 lg:block">
      <button class="btn-ghost w-full !py-2.5 text-sm" @click="clear">
        <PlusIcon class="h-4 w-4" />{{ t('chat.newChat') }}
      </button>
      <h2 class="eyebrow mt-6 px-2">{{ t('chat.topics') }}</h2>
      <TopicsPanel class="mt-2" @pick="pickTopic" />
    </aside>

    <!-- темы: выезжающая панель на телефоне -->
    <Transition name="fade">
      <div v-if="topicsOpen" class="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm lg:hidden" @click="topicsOpen = false" />
    </Transition>
    <aside
      class="fixed inset-y-0 left-0 z-[70] w-[86%] max-w-sm overflow-y-auto bg-page px-4 py-5 shadow-2xl transition-transform duration-500 ease-(--ease-out-quint) lg:hidden"
      :class="topicsOpen ? 'translate-x-0' : '-translate-x-full'"
      :aria-hidden="!topicsOpen"
    >
      <div class="flex items-center justify-between">
        <h2 class="display-title text-lg">{{ t('chat.topics') }}</h2>
        <button class="rounded-xl p-2 text-muted hover:bg-sand" :aria-label="t('nav.closeMenu')" @click="topicsOpen = false">
          <XMarkIcon class="h-5 w-5" />
        </button>
      </div>
      <TopicsPanel class="mt-3" @pick="pickTopic" />
    </aside>

    <section class="flex min-h-0 min-w-0 flex-col">
      <!-- шапка чата -->
      <div class="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-6">
        <div class="min-w-0">
          <h1 class="display-title truncate text-lg">{{ t('chat.title') }}</h1>
          <p class="truncate text-xs text-muted sm:text-sm">{{ t('chat.subtitle') }}</p>
        </div>
        <div class="flex shrink-0 gap-1">
          <button class="btn-ghost !px-3 !py-2 text-sm lg:hidden" @click="topicsOpen = true">
            <ListBulletIcon class="h-4 w-4" /><span class="hidden sm:inline">{{ t('chat.topics') }}</span>
          </button>
          <button v-if="messages.length" class="btn-ghost !px-3 !py-2 text-sm lg:hidden" :aria-label="t('chat.newChat')" @click="clear">
            <PlusIcon class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- лента сообщений -->
      <div ref="scroller" class="flex-1 overflow-y-auto">
        <div class="mx-auto max-w-3xl space-y-5 px-4 py-6 sm:px-6">
          <!-- пустой чат: приветствие и примеры вопросов -->
          <div v-if="!messages.length" class="flex min-h-[55vh] flex-col items-center justify-center text-center">
            <LogoMark class="animate-pop h-16 w-16" />
            <h2 class="display-title animate-rise mt-5 text-2xl" style="animation-delay: 80ms">{{ t('chat.emptyTitle') }}</h2>
            <p class="animate-rise mt-2 max-w-md text-[15px] leading-relaxed text-muted" style="animation-delay: 140ms">{{ t('chat.emptyText') }}</p>
            <div class="mt-7 flex max-w-xl flex-wrap justify-center gap-2">
              <button
                v-for="(q, i) in examples"
                :key="q"
                class="chip animate-pop"
                :style="{ animationDelay: `${220 + i * 80}ms` }"
                @click="submit(q)"
              >
                {{ q }}
              </button>
            </div>
          </div>

          <TransitionGroup name="msg" tag="div" class="space-y-5">
            <ChatBubble
              v-for="m in messages"
              :key="m.id"
              :message="m"
              :last="m.id === lastBotId && !pending"
              @suggest="pickTopic"
              @rate="(useful) => rate(m.id, useful)"
            />
          </TransitionGroup>

          <!-- бот «печатает», пока ждём ответ -->
          <div v-if="pending" class="flex items-center gap-3" role="status" :aria-label="t('chat.typing')">
            <LogoMark class="h-8 w-8 animate-pulse" />
            <div class="flex gap-1.5 rounded-2xl rounded-tl-md border border-line bg-surface px-4 py-3.5">
              <span v-for="i in 3" :key="i" class="typing-dot h-2 w-2 rounded-full bg-primary" :style="{ animationDelay: `${i * 0.15}s` }" />
            </div>
          </div>
        </div>
      </div>

      <!-- поле ввода -->
      <form class="border-t border-line bg-page px-4 pt-3 pb-4 sm:px-6" @submit.prevent="submit()">
        <div class="mx-auto max-w-3xl">
          <div
            class="flex items-end gap-2 rounded-2xl border border-line bg-surface p-2 shadow-sm transition-all duration-300 focus-within:border-primary focus-within:shadow-[0_0_0_4px_var(--primary-soft)]"
          >
            <textarea
              ref="textarea"
              v-model="input"
              rows="1"
              :maxlength="MAX_LENGTH"
              :placeholder="t('chat.placeholder')"
              class="max-h-42 flex-1 resize-none bg-transparent px-2 py-2 text-[15px] text-ink outline-none placeholder:text-faint"
              @keydown="onKeydown"
              @input="resize"
            />
            <span v-if="input.length > MAX_LENGTH * 0.8" class="self-center font-mono text-[11px] text-faint">{{ input.length }}/{{ MAX_LENGTH }}</span>
            <button
              type="submit"
              :disabled="!input.trim() || pending"
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary text-on-primary transition-all duration-200 hover:bg-primary-strong active:scale-90 disabled:cursor-not-allowed disabled:bg-sand disabled:text-faint"
              :aria-label="t('chat.send')"
            >
              <ArrowUpIcon class="h-5 w-5" />
            </button>
          </div>
          <p class="mt-2 text-center text-[11px] text-faint">{{ t('chat.hint') }}</p>
        </div>
      </form>
    </section>
  </div>
</template>
