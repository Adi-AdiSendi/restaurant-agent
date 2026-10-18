import styles from './MicButton.module.css'
import { hasVoice, useVoice } from './useVoice'

interface Props {
  disabled: boolean
  /** Puts what was said into the message box; the guest sends it. */
  onText: (text: string) => void
}

/** Speak instead of typing (English). Hidden where the browser cannot take voice input. */
function MicButton({ disabled, onText }: Props) {
  const { listening, transcribing, error, toggle } = useVoice(onText)
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
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
    </>
  )
}

export default MicButton
