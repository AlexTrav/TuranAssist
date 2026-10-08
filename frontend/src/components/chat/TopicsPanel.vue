<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'
import { useKnowledge } from '../../composables/useKnowledge'
import type { AppLocale } from '../../types'

// все темы бота по группам: нажатие сразу задаёт вопрос по теме
const emit = defineEmits<{ pick: [topic: { intent: string; title: string }] }>()
const { t, locale } = useI18n()
const lang = computed(() => locale.value as AppLocale)
const { groups } = useKnowledge()
const open = ref<string | null>('admission')
const visible = computed(() => groups.value.filter((g) => g.id !== 'service'))
</script>

<template>
  <div>
    <p class="px-2 text-xs text-faint">{{ t('chat.topicsHint') }}</p>
    <ul class="mt-3 space-y-1">
      <li v-for="g in visible" :key="g.id">
        <button
          class="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm font-semibold transition-colors hover:bg-sand"
          :class="open === g.id ? 'text-ink' : 'text-muted'"
          :aria-expanded="open === g.id"
          @click="open = open === g.id ? null : g.id"
        >
          <span>{{ g.title[lang] }} <span class="font-mono text-[11px] font-normal text-faint">{{ g.intents.length }}</span></span>
          <ChevronDownIcon class="h-4 w-4 transition-transform duration-300" :class="open === g.id ? 'rotate-180' : ''" />
        </button>
        <div class="expand" :data-open="open === g.id">
          <div>
            <ul class="mt-0.5 mb-2 space-y-0.5 border-l border-line pl-2 ml-3">
              <li v-for="i in g.intents" :key="i.id">
                <button
                  class="w-full rounded-lg px-2 py-1.5 text-left text-[13px] text-muted transition-all hover:translate-x-0.5 hover:bg-primary-soft hover:text-ink"
                  @click="emit('pick', { intent: i.id, title: i.title[lang] })"
                >
                  {{ i.title[lang] }}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>
