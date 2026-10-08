<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Bars3Icon, MoonIcon, SunIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { useTheme } from '../composables/useTheme'
import LanguageSwitcher from './LanguageSwitcher.vue'
import LogoMark from './icons/LogoMark.vue'

const { t } = useI18n()
const route = useRoute()
const isOpen = ref(false) // раскрыто ли мобильное меню
const { theme, toggleTheme } = useTheme()

const links = computed(() => [
  { to: '/', label: t('nav.home') },
  { to: '/chat', label: t('nav.chat') },
  { to: '/calculator', label: t('nav.calculator') },
  { to: '/knowledge', label: t('nav.knowledge') },
  { to: '/performance', label: t('nav.performance') },
  { to: '/about', label: t('nav.about') },
])

// при переходе на другую страницу мобильное меню закрывается
watch(() => route.path, () => (isOpen.value = false))
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-line bg-page/85 backdrop-blur-md">
    <nav class="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
      <RouterLink to="/" class="group flex shrink-0 items-center gap-2.5">
        <LogoMark class="h-9 w-9 transition-transform duration-300 ease-(--ease-spring) group-hover:-rotate-6 group-hover:scale-105" />
        <span class="font-display text-lg font-bold tracking-tight text-ink">Turan<span class="text-primary">Assist</span></span>
      </RouterLink>

      <ul class="hidden items-center gap-1 lg:flex">
        <li v-for="link in links" :key="link.to">
          <RouterLink
            :to="link.to"
            class="group relative block rounded-lg px-3 py-2 text-[15px] font-medium text-muted transition-colors hover:text-ink"
            exact-active-class="!text-ink"
          >
            {{ link.label }}
            <!-- полоска активного раздела в цвете «Турана» -->
            <span
              class="absolute inset-x-3 -bottom-[13px] h-0.5 origin-left scale-x-0 rounded-full bg-primary transition-transform duration-300 ease-(--ease-out-quint) group-[.router-link-exact-active]:scale-x-100"
            />
          </RouterLink>
        </li>
      </ul>

      <div class="flex items-center gap-1.5">
        <LanguageSwitcher />
        <button
          class="flex h-10 w-10 items-center justify-center rounded-xl text-muted transition-colors hover:bg-sand hover:text-ink"
          :aria-label="theme === 'dark' ? t('nav.themeToLight') : t('nav.themeToDark')"
          @click="toggleTheme"
        >
          <Transition name="fade" mode="out-in">
            <SunIcon v-if="theme === 'dark'" key="sun" class="h-5 w-5" />
            <MoonIcon v-else key="moon" class="h-5 w-5" />
          </Transition>
        </button>
        <button
          class="flex h-10 w-10 items-center justify-center rounded-xl text-muted transition-colors hover:bg-sand hover:text-ink lg:hidden"
          :aria-label="isOpen ? t('nav.closeMenu') : t('nav.openMenu')"
          :aria-expanded="isOpen"
          @click="isOpen = !isOpen"
        >
          <XMarkIcon v-if="isOpen" class="h-6 w-6" />
          <Bars3Icon v-else class="h-6 w-6" />
        </button>
      </div>
    </nav>

    <!-- мобильное меню: разделы крупно, появляются лесенкой -->
    <div class="expand lg:hidden" :data-open="isOpen">
      <div>
        <ul class="flex flex-col gap-1 border-t border-line px-4 pt-3 pb-5">
          <li
            v-for="(link, i) in links"
            :key="link.to"
            :class="isOpen ? 'animate-rise' : 'opacity-0'"
            :style="{ animationDelay: `${i * 40}ms` }"
          >
            <RouterLink
              :to="link.to"
              class="flex items-center justify-between rounded-xl px-3 py-3 font-display text-lg font-semibold text-muted transition-colors hover:bg-sand hover:text-ink"
              exact-active-class="!bg-primary-soft !text-ink"
            >
              {{ link.label }}
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </header>
</template>
