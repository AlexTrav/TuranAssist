<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LINKS } from '../links'
import LogoMark from './icons/LogoMark.vue'

const { t } = useI18n()
const sections = computed(() => [
  { to: '/chat', label: t('nav.chat') },
  { to: '/calculator', label: t('nav.calculator') },
  { to: '/knowledge', label: t('nav.knowledge') },
  { to: '/performance', label: t('nav.performance') },
  { to: '/about', label: t('nav.about') },
])
const links = [
  { href: LINKS.telegram, label: 'Telegram' },
  { href: LINKS.github, label: 'GitHub' },
  { href: LINKS.huggingface, label: 'Hugging Face' },
  { href: LINKS.source, label: 'turan.edu.kz' },
]
</script>

<template>
  <footer class="mt-24 border-t border-line bg-sand/60">
    <div class="mx-auto grid max-w-7xl gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.6fr_1fr_1fr]">
      <div>
        <div class="flex items-center gap-2.5">
          <LogoMark class="h-9 w-9" />
          <span class="font-display text-lg font-bold text-ink">Turan<span class="text-primary">Assist</span></span>
        </div>
        <p class="mt-4 max-w-md text-sm leading-relaxed text-muted">{{ t('footer.tagline') }}</p>
        <p class="mt-3 max-w-md text-xs leading-relaxed text-faint">{{ t('footer.project') }}</p>
      </div>
      <div>
        <h3 class="eyebrow">{{ t('footer.sections') }}</h3>
        <ul class="mt-4 space-y-2 text-sm">
          <li v-for="s in sections" :key="s.to">
            <RouterLink :to="s.to" class="text-muted transition-colors hover:text-primary-strong">{{ s.label }}</RouterLink>
          </li>
        </ul>
      </div>
      <div>
        <h3 class="eyebrow">{{ t('footer.links') }}</h3>
        <ul class="mt-4 space-y-2 text-sm">
          <li v-for="l in links" :key="l.href">
            <a :href="l.href" target="_blank" rel="noopener" class="text-muted transition-colors hover:text-primary-strong">{{ l.label }} ↗</a>
          </li>
        </ul>
      </div>
    </div>
    <!-- бот не выдаёт себя за официальный сервис университета -->
    <div class="border-t border-line">
      <p class="mx-auto max-w-7xl px-4 py-5 text-xs leading-relaxed text-faint sm:px-6">{{ t('footer.disclaimer') }}</p>
    </div>
  </footer>
</template>
