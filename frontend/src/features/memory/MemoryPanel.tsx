import { useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Preference } from '../../api/types'
import CaloriesToday from './CaloriesToday'
import { describe, GROUPS } from './memoryLabels'
import styles from './MemoryPanel.module.css'

interface Props {
  /** Changes after every reply, so the panel reloads what was learned. */
  refreshKey: number
  onUnauthorized: () => void
}

function MemoryPanel({ refreshKey, onUnauthorized }: Props) {
  const [prefs, setPrefs] = useState<Preference[] | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let live = true
    api
      .getPreferences()
      .then((rows) => {
        if (!live) return
        setPrefs(rows)
        setFailed(false)
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        else if (live) setFailed(true)
      })
    return () => {
      live = false
    }
  }, [refreshKey, onUnauthorized])

  const active = prefs?.filter((p) => p.status === 'active') ?? []
  const past = prefs?.filter((p) => p.status !== 'active').slice(0, 6) ?? []
  const goal = active.find((p) => p.kind === 'calories')

  return (
    <aside className={styles.panel} aria-label="What I remember about you">
      <h2 className={styles.title}>What I remember about you</h2>
      {failed && <p className={styles.muted}>Could not load your profile right now.</p>}
      {prefs && active.length === 0 && (
        <p className={styles.muted}>Nothing yet. Tell me what you like, avoid or cannot eat.</p>
      )}
      {GROUPS.map(([kind, label]) => {
        const rows = active.filter((p) => p.kind === kind)
        if (rows.length === 0) return null
        return (
          <section key={kind} className={styles.group}>
            <h3 className={styles.groupTitle}>
              {label}
              {rows[0]?.is_hard && <span className={styles.enforced}>always enforced</span>}
            </h3>
            <ul className={styles.values}>
              {rows.map((p) => (
                <li key={p.id}>{describe(p)}</li>
              ))}
            </ul>
          </section>
        )
      })}
      {goal && <CaloriesToday goal={Number(goal.value)} refreshKey={refreshKey} />}
      {past.length > 0 && (
        <section className={styles.group}>
          <h3 className={styles.groupTitle}>Updated earlier</h3>
          <ul className={styles.history}>
            {past.map((p) => (
              <li key={p.id}>
                <s>{describe(p)}</s>{' '}
                <span className={styles.muted}>
                  ({p.kind}, {p.status})
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </aside>
  )
}

export default MemoryPanel
