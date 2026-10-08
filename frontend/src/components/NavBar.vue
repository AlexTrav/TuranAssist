<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bars3Icon, MoonIcon, SunIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { useTheme } from '../composables/useTheme'
import LanguageSwitcher from './LanguageSwitcher.vue'
import LogoMark from './icons/LogoMark.vue'

const { t } = useI18n()
const isOpen = ref(false) // раскрыто ли мобильное меню
const { theme, toggleTheme } = useTheme()

const links = computed(() => [
  { to: '/', label: t('nav.home') },
  { to: '/chat', label: t('nav.chat') },
  { to: '/performance', label: t('nav.performance') },
  { to: '/about', label: t('nav.about') },
])
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-slate-200/70 bg-slate-50/80 backdrop-blur-md dark:border-slate-800/70 dark:bg-slate-950/80">
    <nav class="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
      <RouterLink to="/" class="flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-slate-50">
        <LogoMark class="h-8 w-8" />
        <span>Turan<span class="text-brand-600 dark:text-brand-400">Assist</span></span>
      </RouterLink>

      <div class="hidden items-center gap-1 md:flex">
        <ul class="flex items-center gap-1">
          <li v-for="link in links" :key="link.to">
            <RouterLink
              :to="link.to"
              class="rounded-full px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-brand-900/40 dark:hover:text-brand-300"
              exact-active-class="!bg-brand-100 !text-brand-800 dark:!bg-brand-900/60 dark:!text-brand-200"
            >
              {{ link.label }}
            </RouterLink>
          </li>
        </ul>
        <LanguageSwitcher class="ml-1" />
        <button
          class="ml-1 flex h-9 w-9 items-center justify-center rounded-full text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          :aria-label="theme === 'dark' ? t('nav.themeToLight') : t('nav.themeToDark')"
          @click="toggleTheme"
        >
          <SunIcon v-if="theme === 'dark'" class="h-5 w-5" />
          <MoonIcon v-else class="h-5 w-5" />
        </button>
      </div>

      <!-- язык, тема и меню на мобильных экранах -->
      <div class="flex items-center gap-1 md:hidden">
        <LanguageSwitcher />
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          :aria-label="theme === 'dark' ? t('nav.themeToLight') : t('nav.themeToDark')"
          @click="toggleTheme"
        >
          <SunIcon v-if="theme === 'dark'" class="h-5 w-5" />
          <MoonIcon v-else class="h-5 w-5" />
        </button>
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          :aria-label="t('nav.openMenu')"
          @click="isOpen = !isOpen"
        >
          <XMarkIcon v-if="isOpen" class="h-5 w-5" />
          <Bars3Icon v-else class="h-5 w-5" />
        </button>
      </div>
    </nav>

    <Transition name="page-fade">
      <ul v-if="isOpen" class="flex flex-col gap-1 border-t border-slate-200 px-5 py-3 md:hidden dark:border-slate-800">
        <li v-for="link in links" :key="link.to">
          <RouterLink
            :to="link.to"
            class="block rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-brand-50 hover:text-brand-700 dark:text-slate-300 dark:hover:bg-brand-900/40"
            exact-active-class="!bg-brand-100 !text-brand-800 dark:!bg-brand-900/60 dark:!text-brand-200"
            @click="isOpen = false"
          >
            {{ link.label }}
          </RouterLink>
        </li>
      </ul>
    </Transition>
  </header>
</template>
