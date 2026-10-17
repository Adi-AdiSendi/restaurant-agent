import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { Order } from '../../api/cartTypes'
import styles from './Orders.module.css'
import { STATUS, when } from './orderLabels'

const REFRESH_MS = 30_000

/** One order: what was bought, at what price, and its status (reloaded until ready). */
function OrderPage() {
  const { id = '' } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined
    const load = () =>
      api.order(Number(id)).then(
        (loaded) => {
          setOrder(loaded)
          if (loaded.status !== 'ready') timer = setTimeout(() => void load(), REFRESH_MS)
        },
        (err: unknown) =>
          setError(err instanceof ApiError ? err.message : 'Could not load this order.'),
      )
    void load()
    return () => clearTimeout(timer)
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
  if (!order) return null
  return (
    <main className={styles.page}>
      <h1 className={styles.title}>
        Order {order.id} · {order.restaurant.name}
      </h1>
      <p>
        <span className={styles[order.status]}>{STATUS[order.status]}</span> ·{' '}
        {order.fulfilment === 'pickup' ? 'Pickup' : 'Dine in'} · {when(order.placed_at)}
      </p>
      <ul className={styles.lines}>
        {order.lines.map((line, n) => (
          <li key={n} className={styles.summary}>
            <span>
              {line.quantity} × {line.item_name}
            </span>
            <span>{[...line.option_names, ...line.removed.map((r) => `no ${r}`)].join(', ')}</span>
            <span>{line.unit_price_sar} SAR each</span>
          </li>
        ))}
      </ul>
      <p className={styles.total}>Total {order.total_sar} SAR · pay at the counter</p>
      <Link to="/orders">All your orders</Link>
    </main>
  )
}

export default OrderPage
