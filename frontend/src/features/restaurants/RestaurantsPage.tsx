import { Link } from 'react-router'

import styles from './RestaurantsPage.module.css'
import { useRestaurants } from './useRestaurants'

/** The home page: pick a restaurant, then browse, chat and order there. */
function RestaurantsPage() {
  const { restaurants, error, reload } = useRestaurants()
  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Where would you like to order from?</h1>
      <p className={styles.subtitle}>
        The assistant remembers your allergies, diet and tastes at every restaurant.
      </p>
      {error && (
        <div className={styles.error} role="alert">
          <span>{error}</span>
          <button className={styles.retry} type="button" onClick={reload}>
            Retry
          </button>
        </div>
      )}
      {restaurants && (
        <ul className={styles.grid}>
          {restaurants.map((r) => (
            <li key={r.slug}>
              <Link
                className={styles.card}
                to={`/r/${r.slug}`}
                style={{ borderTopColor: r.accent_color }}
              >
                <span className={styles.name}>{r.name}</span>
                <span className={styles.cuisine}>{r.cuisine}</span>
                <span className={styles.tagline}>{r.tagline}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default RestaurantsPage
