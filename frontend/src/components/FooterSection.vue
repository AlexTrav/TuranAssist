<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { LINKS } from '../links'

const { t } = useI18n()
</script>

<template>
  <footer class="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
    <div class="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-8 text-sm text-slate-500 dark:text-slate-400">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p>{{ t('footer.tagline') }}</p>
        <div class="flex flex-wrap gap-4 font-medium">
          <a :href="LINKS.telegram" target="_blank" rel="noopener" class="hover:text-brand-600 dark:hover:text-brand-400">Telegram</a>
          <a :href="LINKS.github" target="_blank" rel="noopener" class="hover:text-brand-600 dark:hover:text-brand-400">GitHub</a>
          <a :href="LINKS.huggingface" target="_blank" rel="noopener" class="hover:text-brand-600 dark:hover:text-brand-400">Hugging Face</a>
          <a :href="LINKS.source" target="_blank" rel="noopener" class="hover:text-brand-600 dark:hover:text-brand-400">turan.edu.kz</a>
        </div>
      </div>
      <!-- бот не выдаёт себя за официальный сервис университета -->
      <p class="text-xs">{{ t('footer.disclaimer') }}</p>
    </div>
  </footer>
</template>
