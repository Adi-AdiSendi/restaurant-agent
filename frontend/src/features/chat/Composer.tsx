import { useState, type FormEvent } from 'react'

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
      <button className={styles.send} type="submit" disabled={disabled || !text.trim()}>
        Send
      </button>
    </form>
  )
}

export default Composer
