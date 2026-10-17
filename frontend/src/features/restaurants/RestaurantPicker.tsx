import type { Restaurant } from '../../api/types'
import styles from './RestaurantPicker.module.css'

interface Props {
  restaurants: Restaurant[]
  current: Restaurant | null
  disabled: boolean
  onChoose: (slug: string) => void
}

/** Choosing another restaurant starts a new chat there; memory carries over. */
function RestaurantPicker({ restaurants, current, disabled, onChoose }: Props) {
  return (
    <label className={styles.picker}>
      <span className={styles.label}>Restaurant</span>
      <select
        className={styles.select}
        value={current?.slug ?? ''}
        disabled={disabled || restaurants.length === 0}
        onChange={(e) => onChoose(e.target.value)}
      >
        {restaurants.map((r) => (
          <option key={r.slug} value={r.slug}>
            {r.name} ({r.cuisine.toLowerCase()})
          </option>
        ))}
      </select>
    </label>
  )
}

export default RestaurantPicker
