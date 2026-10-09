<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { useServerStatus } from '../composables/useServerStatus'

const { t } = useI18n()
const { status, wake } = useServerStatus()
</script>

<template>
  <!-- бесплатный Render засыпает после 15 минут простоя – предупреждаем, что первый ответ займёт до минуты.
       Плашка плавает под шапкой: видна на любой странице и при прокрутке, не сдвигает вёрстку чата -->
  <Transition name="fade">
    <div
      v-if="status === 'waking' || status === 'down'"
      class="fixed inset-x-4 top-[4.5rem] z-40 mx-auto w-fit max-w-[calc(100%-2rem)] rounded-2xl border px-4 py-2.5 text-center text-sm shadow-lg backdrop-blur-md"
      :class="status === 'waking' ? 'border-gold/50 bg-gold-soft/95 text-ink' : 'border-danger/40 bg-danger-soft/95 text-danger'"
      role="status"
    >
      <span v-if="status === 'waking'" class="inline-flex items-center gap-2">
        <ArrowPathIcon class="h-4 w-4 animate-spin" />
        {{ t('status.waking') }}
      </span>
      <span v-else class="inline-flex items-center gap-2">
        <ExclamationTriangleIcon class="h-4 w-4" />
        {{ t('status.down') }}
        <button class="font-semibold underline underline-offset-2" @click="wake">{{ t('status.retry') }}</button>
      </span>
    </div>
  </Transition>
</template>
