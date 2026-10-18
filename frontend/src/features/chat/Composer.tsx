import { useState, type FormEvent } from 'react'

import MicButton from '../voice/MicButton'
import styles from './Composer.module.css'

interface Props {
  disabled: boolean
  onSend: (text: string) => void
}

function Composer({ disabled, onSend }: Props) {
  const [text, setText] = useState('')

  function submit(event: FormEvent) {
    event.preventDefault()
    if (!text.trim() || disabled) return
    onSend(text)
    setText('')
  }

  // Auto mode sends what was said; while a reply is pending it waits in the box instead.
  function sendSpoken(spoken: string) {
    if (disabled || !spoken.trim()) return setText(spoken)
    onSend(spoken)
    setText('')
  }

  return (
    <form className={styles.composer} onSubmit={submit}>
      <input
        className={styles.input}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Tell me what you feel like eating…"
        aria-label="Message"
        maxLength={2000}
      />
      <MicButton disabled={disabled} onText={setText} onSend={sendSpoken} />
      <button className={styles.send} type="submit" disabled={disabled || !text.trim()}>
        Send
      </button>
    </form>
  )
}

export default Composer
