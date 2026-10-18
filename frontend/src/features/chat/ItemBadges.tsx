import type { Card } from '../../api/menuTypes'
import { kcalLabel } from '../../components/kcal'
import styles from './ItemCard.module.css'

const SPICE = ['Not spicy', 'Mild', 'Medium', 'Hot']

/** Diet, spice and kcal from the card data, and whether it matches the guest's tastes. */
function ItemBadges({ item }: { item: Card }) {
  const diet = item.is_vegan ? 'Vegan' : item.is_vegetarian ? 'Vegetarian' : null
  return (
    <div className={styles.badges}>
      {diet && <span className={styles.diet}>{diet}</span>}
      <span className={styles.spice}>
        <span aria-hidden="true">{'🌶'.repeat(item.spice_level)}</span>{' '}
        {SPICE[item.spice_level] ?? ''}
      </span>
      {item.kcal !== null && <span className={styles.spice}>{kcalLabel(item.kcal)}</span>}
      {item.liked && <span className={styles.diet}>You like this</span>}
      {item.today_pick && <span className={styles.diet}>Today&apos;s pick for you</span>}
    </div>
  )
}

export default ItemBadges
