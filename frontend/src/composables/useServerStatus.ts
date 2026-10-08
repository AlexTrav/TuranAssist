import { ref } from 'vue'
import { api } from '../api/client'

export type ServerStatus = 'unknown' | 'waking' | 'ready' | 'down'

// если сервер не ответил за это время – скорее всего, бесплатный Render просыпается (до минуты)
const WAKING_AFTER_MS = 2500

// модульный singleton: баннер и чат видят одно состояние
const status = ref<ServerStatus>('unknown')
let pending: Promise<void> | null = null

export function useServerStatus() {
  // будит бэкенд при открытии сайта – к первому вопросу он уже готов
  function wake(): Promise<void> {
    if (pending) return pending
    const slow = setTimeout(() => {
      if (status.value !== 'ready') status.value = 'waking'
    }, WAKING_AFTER_MS)
    pending = api
      .health()
      .then(() => {
        status.value = 'ready'
      })
      .catch(() => {
        status.value = 'down'
      })
      .finally(() => {
        clearTimeout(slow)
        pending = null
      })
    return pending
  }
  return { status, wake }
}
