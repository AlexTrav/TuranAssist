<script setup lang="ts">
import { computed } from 'vue'
import { parseRichText } from '../../utils/richText'

// ответ из базы: абзацы, списки, кликабельные ссылки, телефоны и почта (без v-html)
const props = defineProps<{ text: string }>()
const blocks = computed(() => parseRichText(props.text))
</script>

<template>
  <div class="space-y-2.5 text-[15px] leading-relaxed">
    <template v-for="(block, b) in blocks" :key="b">
      <p v-if="block.type === 'p'" class="break-words">
        <template v-for="(part, i) in block.content" :key="i">
          <a v-if="part.type === 'link'" :href="part.href" target="_blank" rel="noopener" class="link break-all">{{ part.label }}</a>
          <template v-else>{{ part.value }}</template>
        </template>
      </p>
      <ul v-else class="space-y-1.5">
        <li v-for="(item, k) in block.items" :key="k" class="relative pl-4 break-words">
          <span class="absolute top-[0.6em] left-0 h-1.5 w-1.5 rounded-full bg-primary" aria-hidden="true" />
          <template v-for="(part, i) in item" :key="i">
            <a v-if="part.type === 'link'" :href="part.href" target="_blank" rel="noopener" class="link break-all">{{ part.label }}</a>
            <template v-else>{{ part.value }}</template>
          </template>
        </li>
      </ul>
    </template>
  </div>
</template>
