import { useState } from 'react'

import styles from './MicButton.module.css'
import { hasVoice, useVoice } from './useVoice'

interface Props {
  disabled: boolean
  /** Puts what is being said into the message box, to review and send. */
  onText: (text: string) => void
  /** Sends what was said at once (auto mode). */
  onSend: (text: string) => void
}

const AUTO_KEY = 'voice-auto-send'

function savedAuto(): boolean {
  try {
    return localStorage.getItem(AUTO_KEY) === 'on'
  } catch {
    return false
  }
}

/** Speak instead of typing (English). Hidden where the browser cannot take voice input. */
function MicButton({ disabled, onText, onSend }: Props) {
  // Off by default: the guest checks the words before a misheard order is sent.
  const [auto, setAuto] = useState(savedAuto)
  const { listening, transcribing, error, toggle } = useVoice(onText, auto ? onSend : onText)
  function toggleAuto() {
    setAuto(!auto)
    try {
      localStorage.setItem(AUTO_KEY, auto ? 'off' : 'on')
    } catch {
      // Not saved (private window): it still works for this visit.
    }
  }
  if (!hasVoice()) return null
  const label = listening ? 'Stop listening' : transcribing ? 'Working out what you said' : 'Speak'
  return (
    <>
      <button
        className={listening ? styles.micOn : styles.mic}
        type="button"
        aria-label={label}
        aria-pressed={listening}
        disabled={disabled || transcribing}
        onClick={toggle}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true" width="20" height="20">
          <path
            fill="currentColor"
            d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.9V21h2v-2.1a7 7 0 0 0 6-6.9h-2Z"
          />
        </svg>
      </button>
      <button
        className={auto ? styles.autoOn : styles.auto}
        type="button"
        aria-pressed={auto}
        title={auto ? 'Sends what you say at once' : 'Puts what you say in the box to check first'}
        onClick={toggleAuto}
      >
        Auto
      </button>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </>
  )
}

export default MicButton
