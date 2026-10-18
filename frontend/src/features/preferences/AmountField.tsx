import { useState, type FormEvent, type ReactNode } from 'react'

import type { Preference } from '../../api/types'
import styles from './Preferences.module.css'
import type { Edits } from './usePreferences'

interface Props {
  kind: 'budget' | 'calories'
  title: string
  hint: string
  unit: string
  /** Leave out to let the server's range speak (its 422 message is shown). */
  min?: number
  max?: number
  step: number
  current: Preference | undefined
  edits: Edits
  children?: ReactNode
}

/** One number (budget, daily calories). The server checks the range, as it does for the chat.
 * The parent keys it by the saved value, so the box resets after a save. */
function AmountField({ kind, title, hint, unit, min, max, step, current, edits, children }: Props) {
  const [draft, setDraft] = useState(current?.value ?? '')
  const value = draft.trim()
  const save = (event: FormEvent) => {
    event.preventDefault()
    void (current ? edits.change(current.id, value) : edits.add(kind, value))
  }
  return (
    <form className={styles.section} onSubmit={save} aria-label={title}>
      <h2 className={styles.heading}>{title}</h2>
      <p className={styles.hint}>{hint}</p>
      <div className={styles.row}>
        <input
          className={styles.number}
          type="number"
          min={min}
          max={max}
          step={step}
          value={draft}
          aria-label={`${title} in ${unit}`}
          onChange={(event) => setDraft(event.target.value)}
        />
        <span>{unit}</span>
        <button type="submit" disabled={edits.busy || value === '' || value === current?.value}>
          Save
        </button>
        {current && (
          <button type="button" disabled={edits.busy} onClick={() => void edits.remove(current.id)}>
            Clear
          </button>
        )}
      </div>
      {children}
    </form>
  )
}

export default AmountField
