<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowTopRightOnSquareIcon, ChatBubbleLeftRightIcon, ChevronDownIcon, MagnifyingGlassIcon, SparklesIcon } from '@heroicons/vue/24/outline'
import { api } from '../api/client'
import RichText from '../components/chat/RichText.vue'
import { useKnowledge } from '../composables/useKnowledge'
import type { AppLocale, KnowledgeItem } from '../types'

const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const { groups, loadGroups } = useKnowledge()

const items = ref<KnowledgeItem[]>([])
const loading = ref(true)
const loadError = ref(false)
const query = ref('')
const group = ref<string>('all')
const open = ref<string | null>(null)

// база ответов грузится на языке интерфейса и перезагружается при смене языка
async function load() {
  loading.value = true
  try {
    ;[items.value] = await Promise.all([api.knowledge(lang.value), loadGroups()])
    loadError.value = false
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(lang, load)

// умный поиск по смыслу: через паузу в наборе сервер ранжирует темы по запросу («общага» -> «Общежитие»).
// Совпадения по тексту видны сразу; темы, найденные сервером, поднимаются наверх в его порядке
const SEARCH_DELAY_MS = 400
const MIN_SEARCH_LENGTH = 3
const semantic = ref<string[]>([])
let searchTimer: ReturnType<typeof setTimeout> | undefined
watch(query, (value) => {
  clearTimeout(searchTimer)
  semantic.value = []
  const q = value.trim()
  if (q.length < MIN_SEARCH_LENGTH) return
  searchTimer = setTimeout(async () => {
    try {
      const results = await api.search(q)
      if (query.value.trim() === q) semantic.value = results.map((r) => r.id)
    } catch {
      // поиск по смыслу – дополнение: без него остаётся поиск по тексту
    }
  }, SEARCH_DELAY_MS)
})
onUnmounted(() => clearTimeout(searchTimer))

const textMatch = (i: KnowledgeItem, q: string) => i.title.toLowerCase().includes(q) || i.answer.toLowerCase().includes(q)
// тема найдена только по смыслу – в тексте нет набранных слов
const bySense = (i: KnowledgeItem) => {
  const q = query.value.trim().toLowerCase()
  return !!q && semantic.value.includes(i.id) && !textMatch(i, q)
}

const visibleGroups = computed(() => groups.value.filter((g) => g.id !== 'service'))
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  const rank = (i: KnowledgeItem) => {
    const at = semantic.value.indexOf(i.id)
    return at < 0 ? semantic.value.length : at
  }
  return items.value
    .filter(
      (i) =>
        i.group !== 'service' &&
        (group.value === 'all' || i.group === group.value) &&
        (!q || textMatch(i, q) || semantic.value.includes(i.id)),
    )
    .sort((a, b) => rank(a) - rank(b)) // сортировка устойчивая: остальные темы сохраняют порядок базы
})
const total = computed(() => items.value.filter((i) => i.group !== 'service').length)
const countIn = (id: string) => items.value.filter((i) => i.group === id).length

// фрагмент ответа вокруг найденного слова – видно, почему тема попала в выдачу
function snippet(item: KnowledgeItem): { before: string; match: string; after: string } | null {
  const q = query.value.trim().toLowerCase()
  if (!q || item.title.toLowerCase().includes(q)) return null
  const at = item.answer.toLowerCase().indexOf(q)
  if (at < 0) return null
  const start = Math.max(0, at - 50)
  return {
    before: (start ? '…' : '') + item.answer.slice(start, at),
    match: item.answer.slice(at, at + q.length),
    after: item.answer.slice(at + q.length, at + q.length + 70) + '…',
  }
}

function highlight(title: string): { before: string; match: string; after: string } {
  const q = query.value.trim().toLowerCase()
  const at = q ? title.toLowerCase().indexOf(q) : -1
  if (at < 0) return { before: title, match: '', after: '' }
  return { before: title.slice(0, at), match: title.slice(at, at + q.length), after: title.slice(at + q.length) }
}
</script>

<template>
  <div class="mx-auto max-w-5xl px-4 py-12 sm:px-6">
    <p class="eyebrow animate-rise">{{ t('kb.eyebrow') }}</p>
    <h1 class="display-title animate-rise mt-3 text-4xl sm:text-5xl" style="animation-delay: 60ms">{{ t('kb.title') }}</h1>
    <p class="animate-rise mt-4 max-w-2xl text-lg text-muted" style="animation-delay: 120ms">{{ t('kb.subtitle') }}</p>

    <!-- поиск и группы -->
    <div class="animate-rise sticky top-16 z-10 -mx-4 mt-8 bg-page/90 px-4 py-3 backdrop-blur-md sm:-mx-6 sm:px-6" style="animation-delay: 180ms">
      <label class="relative block">
        <MagnifyingGlassIcon class="pointer-events-none absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-faint" />
        <input
          v-model="query"
          type="search"
          :placeholder="t('kb.search')"
          class="w-full rounded-2xl border border-line bg-surface py-3.5 pr-4 pl-12 text-base text-ink shadow-sm outline-none transition-all placeholder:text-faint focus:border-primary focus:shadow-[0_0_0_4px_var(--primary-soft)]"
        />
      </label>
      <div class="mt-3 flex gap-2 overflow-x-auto pb-1">
        <button class="chip shrink-0" :class="group === 'all' ? '!border-primary !bg-primary !text-on-primary' : ''" @click="group = 'all'">
          {{ t('kb.all') }} <span class="font-mono text-[11px] opacity-70">{{ total }}</span>
        </button>
        <button
          v-for="g in visibleGroups"
          :key="g.id"
          class="chip shrink-0"
          :class="group === g.id ? '!border-primary !bg-primary !text-on-primary' : ''"
          @click="group = g.id"
        >
          {{ g.title[lang] }} <span class="font-mono text-[11px] opacity-70">{{ countIn(g.id) }}</span>
        </button>
      </div>
    </div>

    <p v-if="loadError" class="mt-8 text-danger">{{ t('apiErrors.network') }}</p>
    <div v-else-if="loading" class="mt-6 space-y-3">
      <div v-for="i in 6" :key="i" class="card h-16 animate-pulse bg-sand/50" />
    </div>
    <template v-else>
      <p class="mt-4 font-mono text-xs text-faint">{{ t('kb.found', { n: filtered.length, total }) }}</p>
      <TransitionGroup tag="ul" name="msg" class="mt-3 space-y-3">
        <li v-for="item in filtered" :key="item.id" class="card overflow-hidden transition-colors" :class="open === item.id ? 'border-steel' : ''">
          <button class="flex w-full items-start justify-between gap-4 p-5 text-left" :aria-expanded="open === item.id" @click="open = open === item.id ? null : item.id">
            <span class="min-w-0">
              <span class="flex flex-wrap items-center gap-2">
                <span class="text-[11px] font-semibold tracking-wide text-primary-strong uppercase">{{ t(`groups.${item.group}`) }}</span>
                <span v-if="bySense(item)" class="inline-flex items-center gap-1 rounded-full bg-gold-soft px-2 py-0.5 text-[11px] font-medium text-ink">
                  <SparklesIcon class="h-3 w-3" />{{ t('kb.bySense') }}
                </span>
              </span>
              <span class="mt-0.5 block font-display text-lg font-semibold text-ink">
                {{ highlight(item.title).before }}<mark v-if="highlight(item.title).match" class="rounded bg-gold-soft px-0.5 text-ink">{{ highlight(item.title).match }}</mark>{{ highlight(item.title).after }}
              </span>
              <span v-if="snippet(item)" class="mt-1 block text-sm text-muted">
                {{ snippet(item)!.before }}<mark class="rounded bg-gold-soft px-0.5 text-ink">{{ snippet(item)!.match }}</mark>{{ snippet(item)!.after }}
              </span>
            </span>
            <ChevronDownIcon class="mt-6 h-5 w-5 shrink-0 text-faint transition-transform duration-300" :class="open === item.id ? 'rotate-180 text-primary' : ''" />
          </button>
          <div class="expand" :data-open="open === item.id">
            <div>
              <div class="border-t border-line px-5 pt-4 pb-5">
                <RichText :text="item.answer" class="text-ink" />
                <div class="mt-4 flex flex-wrap gap-2">
                  <RouterLink :to="{ path: '/chat', query: { q: item.title } }" class="btn-primary !px-4 !py-2 text-sm">
                    <ChatBubbleLeftRightIcon class="h-4 w-4" />{{ t('common.askInChat') }}
                  </RouterLink>
                  <a v-if="item.source_url" :href="item.source_url" target="_blank" rel="noopener" class="btn-ghost !px-4 !py-2 text-sm">
                    {{ t('common.source') }}<ArrowTopRightOnSquareIcon class="h-4 w-4" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </li>
      </TransitionGroup>
      <p v-if="!filtered.length" class="card mt-3 p-8 text-center text-muted">{{ t('kb.empty') }}</p>
    </template>
  </div>
</template>
