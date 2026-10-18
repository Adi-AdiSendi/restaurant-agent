import type { Preference } from '../../api/types'
import { describe } from '../memory/memoryLabels'
import styles from './FactChips.module.css'
import type { Edits } from './usePreferences'

/** Saved facts as chips, each with a remove button. */
function FactChips({ rows, edits }: { rows: Preference[]; edits: Edits }) {
  if (rows.length === 0) return null
  return (
    <ul className={styles.chips}>
      {rows.map((row) => (
        <li key={row.id}>
          {describe(row)}
          <button
            className={styles.x}
            type="button"
            aria-label={`Remove ${describe(row)}`}
            disabled={edits.busy}
            onClick={() => void edits.remove(row.id)}
          >
            ×
          </button>
        </li>
      ))}
    </ul>
  )
}

export default FactChips
