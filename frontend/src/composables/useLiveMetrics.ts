import { onMounted, onUnmounted, ref } from 'vue'
import { api, ApiError } from '../api/client'
import type { LiveMetrics } from '../types'

// опрос живых метрик бэкенда; на скрытой вкладке опрос пропускается, чтобы не будить сервис зря
export function useLiveMetrics(intervalMs = 3000) {
  const metrics = ref<LiveMetrics | null>(null)
  const error = ref<string | null>(null)
  let timer: ReturnType<typeof setInterval> | undefined

  async function refresh() {
    if (document.hidden) return
    try {
      metrics.value = await api.metrics()
      error.value = null
    } catch (err) {
      error.value = err instanceof ApiError ? err.code : 'network'
    }
  }

  onMounted(() => {
    refresh()
    timer = setInterval(refresh, intervalMs)
  })
  onUnmounted(() => clearInterval(timer))

  return { metrics, error, refresh }
}
