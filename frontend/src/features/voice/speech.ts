// The browser's own speech recognition (Chrome, Edge), English only. Ported from
// Aviation-Services/site/concierge/speech.js.

interface RecognitionResult {
  isFinal: boolean
  0: { transcript: string }
}

interface RecognitionEvent {
  resultIndex: number
  results: ArrayLike<RecognitionResult>
}

/** The part of the Web Speech API this app uses; TypeScript's DOM types lack it. */
export interface Recognition {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((event: RecognitionEvent) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

type RecognitionClass = new () => Recognition

function recognitionClass(): RecognitionClass | null {
  const w = window as unknown as Record<string, RecognitionClass | undefined>
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null
}

export const isSpeechSupported = () => recognitionClass() !== null

interface Handlers {
  onInterim: (text: string) => void
  onFinal: (text: string) => void
  onError: (error: string) => void
  onEnd: () => void
}

/** One utterance: live text while speaking, then the final text. */
export function createRecognizer(handlers: Handlers): Recognition | null {
  const Recognizer = recognitionClass()
  if (!Recognizer) return null
  const rec = new Recognizer()
  rec.lang = 'en-US'
  rec.interimResults = true
  rec.continuous = false
  rec.onresult = (event) => {
    let interim = ''
    let final = ''
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i]
      if (!result) continue
      if (result.isFinal) final += result[0].transcript
      else interim += result[0].transcript
    }
    if (interim) handlers.onInterim(interim)
    if (final) handlers.onFinal(final.trim())
  }
  rec.onerror = (event) => handlers.onError(event.error)
  rec.onend = handlers.onEnd
  return rec
}
