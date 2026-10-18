import { useEffect, useState } from 'react'

import { api } from '../../api/client'
import type { Today } from '../../api/types'
import styles from './MemoryPanel.module.css'

interface Props {
  /** The guest's daily goal in kcal. */
  goal: number
  refreshKey: number
}

/** Today's ordered kcal against the goal (estimates). Soft: nothing is blocked. */
function CaloriesToday({ goal, refreshKey }: Props) {
  const [today, setToday] = useState<Today | null>(null)

  useEffect(() => {
    let live = true
    api
      .today()
      .then((t) => live && setToday(t))
      .catch(() => undefined)
    return () => {
      live = false
    }
  }, [refreshKey])

  if (!today) return null
  return (
    <p className={styles.muted}>
      <label>
        Today: {today.kcal.toLocaleString('en')} of {goal.toLocaleString('en')} kcal ordered
        (estimates)
        <progress className={styles.progress} max={goal} value={Math.min(today.kcal, goal)} />
      </label>
    </p>
  )
}

export default CaloriesToday
