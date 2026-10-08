<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { ArrowPathIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import { useServerStatus } from '../composables/useServerStatus'

const { t } = useI18n()
const { status, wake } = useServerStatus()
</script>

<template>
  <!-- бесплатный Render засыпает после 15 минут простоя – предупреждаем, что первый ответ займёт до минуты -->
  <Transition name="page-fade">
    <div
      v-if="status === 'waking' || status === 'down'"
      class="border-b px-5 py-2 text-center text-sm"
      :class="
        status === 'waking'
          ? 'border-accent-200 bg-accent-100 text-accent-700 dark:border-accent-700/40 dark:bg-accent-700/20 dark:text-accent-200'
          : 'border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300'
      "
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
