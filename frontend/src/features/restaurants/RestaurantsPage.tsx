import type { CSSProperties } from 'react'
import { Link } from 'react-router'

import Skeleton from '../../components/Skeleton'

import styles from './RestaurantsPage.module.css'
import Storefront from '../../components/Storefront'
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
      {!restaurants && !error && <Skeleton count={6} label="Loading the restaurants" />}
      {restaurants && (
        <ul className={styles.list}>
          {restaurants.map((r) => (
            <li key={r.slug}>
              <Link
                className={styles.card}
                to={`/r/${r.slug}`}
                style={{ '--accent': r.accent_color } as CSSProperties}
              >
                <Storefront slug={r.slug} />
                <span className={styles.details}>
                  <span className={styles.name}>{r.name}</span>
                  <span className={styles.cuisine}>{r.cuisine}</span>
                  <span className={styles.tagline}>{r.tagline}</span>
                  <span className={styles.open} aria-hidden="true">
                    See the menu →
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </main>
  )
}

export default RestaurantsPage
