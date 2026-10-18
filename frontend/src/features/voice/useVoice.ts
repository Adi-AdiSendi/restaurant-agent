import { useCallback, useEffect, useRef, useState } from 'react'

import { ApiError } from '../../api/errors'
import { transcribe } from '../../api/transcribe'
import { isRecordingSupported, createRecorder, type Recorder } from './record'
import { createRecognizer, isSpeechSupported, type Recognition } from './speech'

/** Whether this browser can take voice input at all. */
export const hasVoice = () => isSpeechSupported() || isRecordingSupported()

export const MIC_BLOCKED = 'Microphone blocked: allow it in your browser to speak your order.'
export const NOT_HEARD = "Didn't catch that, please try again."

/** Voice into the message box: live text while speaking, then `onDone` with the final
 * text (the box to review, or straight to Send in auto mode). Ported from
 * Aviation-Services useVoice.js. */
export function useVoice(setText: (text: string) => void, onDone: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const active = useRef<Recognition | Recorder | null>(null)

  const stop = useCallback(() => {
    active.current?.stop()
    active.current = null
    setListening(false)
  }, [])

  useEffect(() => () => active.current?.stop(), [])

  async function fromRecording(audio: Blob) {
    setListening(false)
    if (audio.size === 0) return setError(NOT_HEARD)
    setTranscribing(true)
    try {
      const text = await transcribe(audio)
      if (text) onDone(text)
      else setError(NOT_HEARD)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : NOT_HEARD)
    } finally {
      setTranscribing(false)
    }
  }

  function toggle() {
    if (listening) return stop()
    setError(null)
    const fail = (message: string) => {
      setError(message)
      setListening(false)
    }
    const recognizer = isSpeechSupported()
      ? createRecognizer({
          onInterim: setText,
          onFinal: onDone,
          onError: (code) => fail(code === 'not-allowed' ? MIC_BLOCKED : NOT_HEARD),
          onEnd: () => setListening(false),
        })
      : createRecorder(
          (audio) => void fromRecording(audio),
          () => fail(MIC_BLOCKED),
        )
    if (!recognizer) return
    active.current = recognizer
    setListening(true)
    void recognizer.start()
  }

  return { listening, transcribing, error, toggle }
}
