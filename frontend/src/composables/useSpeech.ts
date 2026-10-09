import { onUnmounted, ref } from 'vue'
import type { AppLocale } from '../types'

// голосовой ввод через Web Speech API браузера (Chrome, Edge, Safari; в Firefox его нет – кнопка скрыта).
// Речь распознаёт сам браузер, на наш сервер уходит только готовый текст вопроса

// минимальные типы: SpeechRecognition есть не во всех версиях lib.dom
interface RecognitionResult {
  isFinal: boolean
  0: { transcript: string }
}
interface RecognitionEvent {
  resultIndex: number
  results: ArrayLike<RecognitionResult>
}
interface Recognition {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((e: RecognitionEvent) => void) | null
  onerror: ((e: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}
type RecognitionCtor = new () => Recognition

const SPEECH_LANGS: Record<AppLocale, string> = { ru: 'ru-RU', kk: 'kk-KZ', en: 'en-US' }

function recognitionCtor(): RecognitionCtor | null {
  if (typeof window === 'undefined') return null
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export function useSpeech() {
  const supported = recognitionCtor() !== null
  const listening = ref(false)
  const error = ref('') // not-allowed, no-speech, audio-capture, network… – текст подставляет интерфейс
  let recognition: Recognition | null = null

  // onText получает весь распознанный текст: сначала промежуточный, затем окончательный
  function start(locale: AppLocale, onText: (text: string, final: boolean) => void) {
    const Ctor = recognitionCtor()
    if (!Ctor || listening.value) return
    error.value = ''
    recognition = new Ctor()
    recognition.lang = SPEECH_LANGS[locale]
    recognition.interimResults = true // текст появляется в поле прямо во время речи
    recognition.continuous = false // одна фраза – один вопрос; пауза завершает запись
    recognition.onresult = (e) => {
      let text = ''
      let final = true
      for (let i = 0; i < e.results.length; i++) {
        text += e.results[i][0].transcript
        if (!e.results[i].isFinal) final = false
      }
      onText(text.trim(), final)
    }
    recognition.onerror = (e) => {
      if (e.error !== 'aborted') error.value = e.error
    }
    recognition.onend = () => {
      listening.value = false
      recognition = null
    }
    try {
      recognition.start()
      listening.value = true
    } catch {
      error.value = 'start-failed'
      recognition = null
    }
  }

  function stop() {
    recognition?.stop()
  }

  onUnmounted(() => recognition?.abort())
  return { supported, listening, error, start, stop }
}
