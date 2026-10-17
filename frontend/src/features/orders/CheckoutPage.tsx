import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { Fulfilment } from '../../api/cartTypes'
import { useCart } from '../cart/cartContext'
import CartLineRow from '../cart/CartLineRow'
import FulfilmentChoice from './FulfilmentChoice'
import PlaceConfirm from './PlaceConfirm'
import styles from './Orders.module.css'

/** Review the cart and place the order. Only this button places an order (ADR 0019). */
function CheckoutPage() {
  const { cart, error: loadError, refresh } = useCart()
  const navigate = useNavigate()
  const [fulfilment, setFulfilment] = useState<Fulfilment>('pickup')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conflict, setConflict] = useState<{ message: string; reasons: string[] } | null>(null)

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function place(acceptedReasons: string[]) {
    setBusy(true)
    setError(null)
    try {
      const order = await api.placeOrder(fulfilment, acceptedReasons)
      await refresh()
      void navigate(`/orders/${order.id}`)
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail : null
      if (detail?.code === 'conflict')
        setConflict({ message: detail.message, reasons: detail.reasons ?? [] })
      else setError(err instanceof ApiError ? err.message : 'Could not place the order.')
      void refresh()
      setBusy(false)
    }
  }

  if (!cart) {
    return loadError ? (
      <main className={styles.page}>
        <p className={styles.error} role="alert">
          {loadError}
        </p>
        <button type="button" onClick={() => void refresh()}>
          Retry
        </button>
      </main>
    ) : null
  }
  if (cart.lines.length === 0) {
    return (
      <main className={styles.page}>
        <h1 className={styles.title}>Checkout</h1>
        <p>
          Your cart is empty. <Link to="/">Pick a restaurant</Link>.
        </p>
      </main>
    )
  }
  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Checkout · {cart.restaurant?.name}</h1>
      <ul className={styles.lines}>
        {cart.lines.map((line) => (
          <CartLineRow key={line.id} line={line} readOnly />
        ))}
      </ul>
      <p className={styles.total}>Total {cart.total_sar} SAR</p>
      <FulfilmentChoice value={fulfilment} onChange={setFulfilment} />
      <p className={styles.note}>Pay at the counter. This prototype takes no payment.</p>
      {conflict && (
        <PlaceConfirm
          message={conflict.message}
          busy={busy}
          onBack={() => setConflict(null)}
          onPlace={() => void place(conflict.reasons)}
        />
      )}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      <button
        className={styles.place}
        type="button"
        disabled={busy || conflict !== null}
        onClick={() => void place([])}
      >
        Place order · {cart.total_sar} SAR
      </button>
    </main>
  )
}

export default CheckoutPage
