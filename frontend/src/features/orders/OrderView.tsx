import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { Order } from '../../api/cartTypes'
import styles from './Orders.module.css'
import OrderDetail from './OrderDetail'

export const REFRESH_MS = 30_000

/** One order: what was bought, at what price, and its status (reloaded until ready). */
function OrderView({ id }: { id: number }) {
  const [order, setOrder] = useState<Order | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // A response after unmount sets no state and schedules no reload.
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    const load = () =>
      api.order(id).then(
        (loaded) => {
          if (cancelled) return
          setOrder(loaded)
          if (loaded.status !== 'ready') timer = setTimeout(() => void load(), REFRESH_MS)
        },
        (err: unknown) => {
          if (!cancelled)
            setError(err instanceof ApiError ? err.message : 'Could not load this order.')
        },
      )
    void load()
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [id])

  if (error) {
    return (
      <main className={styles.page}>
        <p className={styles.error} role="alert">
          {error}
        </p>
        <Link to="/orders">Your orders</Link>
      </main>
    )
  }
  return order ? <OrderDetail order={order} /> : null
}

export default OrderView
