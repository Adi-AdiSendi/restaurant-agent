import type { Preference } from '../../api/types'
import { describe } from './memoryLabels'
import styles from './MemoryPanel.module.css'

/** Facts that were replaced or removed, struck through: memory changes, it is not stacked. */
function PastFacts({ rows }: { rows: Preference[] }) {
  if (rows.length === 0) return null
  return (
    <section className={styles.group}>
      <h3 className={styles.groupTitle}>Updated earlier</h3>
      <ul className={styles.history}>
        {rows.map((p) => (
          <li key={p.id}>
            <s>{describe(p)}</s>{' '}
            <span className={styles.muted}>
              ({p.kind}, {p.status})
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default PastFacts
