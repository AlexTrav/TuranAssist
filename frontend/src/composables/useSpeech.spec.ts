import { afterEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'
import ru from '../locales/ru'
import { useSpeech } from './useSpeech'

// поддельный распознаватель браузера: тест сам «говорит» за пользователя
class FakeRecognition {
  static last: FakeRecognition
  lang = ''
  interimResults = false
  continuous = true
  onresult: ((e: unknown) => void) | null = null
  onerror: ((e: { error: string }) => void) | null = null
  onend: (() => void) | null = null
  start = vi.fn()
  stop = vi.fn(() => this.onend?.())
  abort = vi.fn()
  constructor() {
    FakeRecognition.last = this
  }
  say(parts: [string, boolean][]) {
    this.onresult?.({ resultIndex: 0, results: parts.map(([transcript, isFinal]) => ({ isFinal, 0: { transcript } })) })
  }
}

afterEach(() => vi.unstubAllGlobals())

describe('голосовой ввод', () => {
  it('без Web Speech API кнопка не показывается', () => {
    expect(useSpeech().supported).toBe(false)
  })

  it('распознаёт на языке интерфейса и отдаёт промежуточный и окончательный текст', () => {
    vi.stubGlobal('webkitSpeechRecognition', FakeRecognition)
    const speech = useSpeech()
    const got: [string, boolean][] = []
    speech.start('kk', (text, final) => got.push([text, final]))
    const rec = FakeRecognition.last
    expect(speech.supported).toBe(true)
    expect(speech.listening.value).toBe(true)
    expect(rec.lang).toBe('kk-KZ')
    expect(rec.interimResults).toBe(true)
    rec.say([['жатақхана', false]])
    rec.say([['жатақхана бар ма', true]])
    expect(got).toEqual([['жатақхана', false], ['жатақхана бар ма', true]])
    speech.stop()
    expect(speech.listening.value).toBe(false)
  })

  it('ошибка доступа к микрофону переводится, отмена записи ошибкой не считается', () => {
    vi.stubGlobal('webkitSpeechRecognition', FakeRecognition)
    const speech = useSpeech()
    speech.start('ru', () => {})
    FakeRecognition.last.onerror?.({ error: 'aborted' })
    expect(speech.error.value).toBe('')
    FakeRecognition.last.onerror?.({ error: 'not-allowed' })
    expect(speech.error.value).toBe('not-allowed')
    const { t } = createI18n({ legacy: false, locale: 'ru', messages: { ru } }).global
    expect(t(`chat.voiceErrors.${speech.error.value}`)).toBe(ru.chat.voiceErrors['not-allowed'])
  })
})
