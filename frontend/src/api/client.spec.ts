import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiError, listenServer, type ServerSignal } from './client'

function collect(): ServerSignal[] {
  const signals: ServerSignal[] = []
  listenServer((s) => signals.push(s))
  return signals
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('сигналы о состоянии сервера', () => {
  it('ответ сервера – «готов», даже если это ошибка 4xx', async () => {
    const signals = collect()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{"detail":{"code":"unknown_intent"}}', { status: 404 })))
    await expect(api.answer('nope', 'ru')).rejects.toMatchObject({ code: 'unknown_intent' })
    expect(signals).toEqual(['ok'])
  })

  it('502/503/504 и обрыв связи – сервер недоступен или просыпается', async () => {
    const signals = collect()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 503 })))
    await expect(api.intents()).rejects.toEqual(new ApiError('waking', 503))
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(api.intents()).rejects.toMatchObject({ code: 'network' })
    expect(signals).toEqual(['fail', 'fail'])
  })

  it('долгий ответ – сервер просыпается; нагрузочный тест так не считается', async () => {
    vi.useFakeTimers()
    const signals = collect()
    const replies: ((r: Response) => void)[] = []
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>((resolve) => replies.push(resolve))))
    const chat = api.chat('привет')
    const bench = api.benchmark()
    await vi.advanceTimersByTimeAsync(3000)
    expect(signals).toEqual(['slow']) // только от чата
    replies.forEach((reply) => reply(new Response('{}')))
    await Promise.all([chat, bench])
    expect(signals).toEqual(['slow', 'ok', 'ok'])
  })
})
