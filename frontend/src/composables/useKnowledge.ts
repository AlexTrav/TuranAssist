import { ref } from 'vue'
import { api } from '../api/client'
import type { AppLocale, GroupInfo, TuitionCatalog } from '../types'

// справочники с бэкенда грузятся один раз на вкладку: темы бота (53 интента в 8 группах) и цены
const groups = ref<GroupInfo[]>([])
const catalog = ref<TuitionCatalog | null>(null)
let groupsLoading: Promise<void> | null = null
let catalogLoading: Promise<void> | null = null

export function useKnowledge() {
  function loadGroups(): Promise<void> {
    groupsLoading ??= api
      .intents()
      .then((data) => {
        groups.value = data
      })
      .catch((err) => {
        groupsLoading = null // повторим при следующем обращении
        throw err
      })
    return groupsLoading
  }

  function loadCatalog(): Promise<void> {
    catalogLoading ??= api
      .tuition()
      .then((data) => {
        catalog.value = data
      })
      .catch((err) => {
        catalogLoading = null
        throw err
      })
    return catalogLoading
  }

  function titleOf(intent: string, lang: AppLocale): string {
    for (const g of groups.value) {
      const found = g.intents.find((i) => i.id === intent)
      if (found) return found.title[lang]
    }
    return intent
  }

  function groupOf(intent: string): GroupInfo | undefined {
    return groups.value.find((g) => g.intents.some((i) => i.id === intent))
  }

  // «Также спрашивают»: следующие темы той же группы по кругу – соседние по смыслу вопросы
  function related(intent: string, count = 3) {
    const group = groupOf(intent)
    if (!group || group.id === 'service') return []
    const list = group.intents
    const at = list.findIndex((i) => i.id === intent)
    return Array.from({ length: Math.min(count, list.length - 1) }, (_, k) => list[(at + 1 + k) % list.length])
  }

  function programName(id: string, lang: AppLocale): string {
    return catalog.value?.programs.find((p) => p.id === id)?.name[lang] ?? id
  }

  return { groups, catalog, loadGroups, loadCatalog, titleOf, groupOf, related, programName }
}
