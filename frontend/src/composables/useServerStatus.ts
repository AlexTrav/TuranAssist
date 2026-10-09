import { ref } from 'vue'
import { api, listenServer } from '../api/client'

export type ServerStatus = 'unknown' | 'waking' | 'ready' | 'down'

// модульный singleton: плашка и все страницы видят одно состояние
const status = ref<ServerStatus>('unknown')
let pending: Promise<void> | null = null

// состояние обновляет любой запрос к API – чат, калькулятор, база знаний, метрики:
// долгий ответ – сервер просыпается, ответ пришёл – готов, нет связи или 502/503/504 – недоступен
listenServer((signal) => {
  status.value = signal === 'slow' ? 'waking' : signal === 'ok' ? 'ready' : 'down'
})

export function useServerStatus() {
  // будит бэкенд при открытии сайта – к первому вопросу он уже готов
  function wake(): Promise<void> {
    pending ??= api
      .health()
      .then(() => {})
      .catch(() => {})
      .finally(() => {
        pending = null
      })
    return pending
  }
  return { status, wake }
}
