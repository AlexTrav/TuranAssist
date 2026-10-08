<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import FooterSection from './components/FooterSection.vue'
import NavBar from './components/NavBar.vue'
import ServerStatusBanner from './components/ServerStatusBanner.vue'
import { useServerStatus } from './composables/useServerStatus'

const route = useRoute()
const { wake } = useServerStatus()
onMounted(wake) // будим бэкенд сразу при открытии сайта – к первому вопросу он уже проснётся
</script>

<template>
  <div class="flex min-h-dvh flex-col">
    <NavBar />
    <ServerStatusBanner />
    <main class="flex-1">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
    <FooterSection v-if="!route.meta.fullHeight" />
  </div>
</template>
