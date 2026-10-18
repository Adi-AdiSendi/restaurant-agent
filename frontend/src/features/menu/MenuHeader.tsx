import type { Restaurant } from '../../api/menuTypes'
import DishPhoto from '../../components/DishPhoto'
import styles from './MenuHeader.module.css'

/** The restaurant's cover, name and tagline; an empty line while the menu loads. */
function MenuHeader({ restaurant }: { restaurant: Restaurant | null }) {
  return (
    <header className={styles.head}>
      {restaurant && (
        <div className={styles.cover}>
          <DishPhoto photo={restaurant.photo} icon="🍽️" size="thumb" />
        </div>
      )}
      <div>
        <h1 className={styles.title}>{restaurant?.name ?? ' '}</h1>
        {restaurant && <p className={styles.tagline}>{restaurant.tagline}</p>}
      </div>
    </header>
  )
}

export default MenuHeader
