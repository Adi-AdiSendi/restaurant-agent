import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { OrderSummary } from '../../api/cartTypes'
import OrderCard from './OrderCard'
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
      {orders && orders.length > 0 && (
        <p className={styles.note}>
          {orders.length} {orders.length === 1 ? 'order' : 'orders'} ·{' '}
          {orders.reduce((sum, o) => sum + Number(o.total_sar), 0).toFixed(2)} SAR spent in all
        </p>
      )}
      <ul className={styles.history}>
        {orders?.map((o) => (
          <li key={o.id}>
            <OrderCard order={o} />
          </li>
        ))}
      </ul>
    </main>
  )
}

export default OrdersPage
