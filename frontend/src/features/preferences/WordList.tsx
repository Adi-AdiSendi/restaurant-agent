import { useState, type FormEvent } from 'react'

import type { Preference } from '../../api/types'
import FactChips from './FactChips'
import styles from './Preferences.module.css'
import type { Edits } from './usePreferences'

interface Props {
  kind: 'like' | 'dislike'
  title: string
  hint: string
  placeholder: string
  rows: Preference[]
  edits: Edits
}

/** Foods the guest likes or dislikes, in their own words. Liking a disliked food
 * replaces the dislike, as in the chat. */
function WordList({ kind, title, hint, placeholder, rows, edits }: Props) {
  const [draft, setDraft] = useState('')
  const add = async (event: FormEvent) => {
    event.preventDefault()
    if (await edits.add(kind, draft)) setDraft('')
  }
  return (
    <form className={styles.section} onSubmit={(event) => void add(event)} aria-label={title}>
      <h2 className={styles.heading}>{title}</h2>
      <p className={styles.hint}>{hint}</p>
      <FactChips rows={rows} edits={edits} />
      <div className={styles.row}>
        <input
          value={draft}
          maxLength={60}
          placeholder={placeholder}
          aria-label={`Add to ${title.toLowerCase()}`}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit" disabled={edits.busy || draft.trim() === ''}>
          Add
        </button>
      </div>
    </form>
  )
}

export default WordList
