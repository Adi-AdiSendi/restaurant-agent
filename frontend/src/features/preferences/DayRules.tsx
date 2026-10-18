import { useState, type FormEvent } from 'react'

import type { Preference } from '../../api/types'
import { plainLabel } from '../memory/memoryLabels'
import FactChips from './FactChips'
import styles from './Preferences.module.css'
import type { Edits } from './usePreferences'

interface Props {
  kind: 'day_dislike' | 'day_like'
  title: string
  hint: string
  weekdays: string[]
  rows: Preference[]
  edits: Edits
}

/** Foods avoided or wanted on one weekday, stored as "friday: fish". Soft: never a block. */
function DayRules({ kind, title, hint, weekdays, rows, edits }: Props) {
  const [day, setDay] = useState(weekdays[4] ?? 'friday')
  const [food, setFood] = useState('')
  const add = async (event: FormEvent) => {
    event.preventDefault()
    if (await edits.add(kind, `${day}: ${food}`)) setFood('')
  }
  return (
    <form className={styles.section} onSubmit={(event) => void add(event)} aria-label={title}>
      <h2 className={styles.heading}>{title}</h2>
      <p className={styles.hint}>{hint}</p>
      <FactChips rows={rows} edits={edits} />
      <div className={styles.row}>
        <select aria-label={`${title}: day`} value={day} onChange={(e) => setDay(e.target.value)}>
          {weekdays.map((weekday) => (
            <option key={weekday} value={weekday}>
              {plainLabel(weekday)}s
            </option>
          ))}
        </select>
        <input
          value={food}
          maxLength={49}
          placeholder={kind === 'day_like' ? 'fish' : 'meat'}
          aria-label={`${title}: food`}
          onChange={(event) => setFood(event.target.value)}
        />
        <button type="submit" disabled={edits.busy || food.trim() === ''}>
          Add
        </button>
      </div>
    </form>
  )
}

export default DayRules
