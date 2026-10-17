import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { OrderSummary } from '../../api/cartTypes'
import { STATUS, when } from './orderLabels'
import styles from './Orders.module.css'

/** The guest's own orders, newest first. */
function OrdersPage() {
  const [orders, setOrders] = useState<OrderSummary[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .orders()
      .then(setOrders, (err: unknown) =>
        setError(err instanceof ApiError ? err.message : 'Could not load your orders.'),
      )
  }, [])

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Your orders</h1>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {orders?.length === 0 && (
        <p>
          No orders yet. <Link to="/">Pick a restaurant</Link>.
        </p>
      )}
      <ul className={styles.lines}>
        {orders?.map((o) => (
          <li key={o.id} className={styles.summary}>
            <Link to={`/orders/${o.id}`}>
              Order {o.id} · {o.restaurant.name}
            </Link>
            <span>
              {o.item_count} items · {o.total_sar} SAR · {when(o.placed_at)}
            </span>
            <span className={styles[o.status]}>{STATUS[o.status]}</span>
          </li>
        ))}
      </ul>
    </main>
  )
}

export default OrdersPage
