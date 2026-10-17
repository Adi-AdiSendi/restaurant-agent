import { useState } from 'react'
import { Link, useNavigate } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { Fulfilment } from '../../api/cartTypes'
import { useCart } from '../cart/cartContext'
import CartLineRow from '../cart/CartLineRow'
import FulfilmentChoice from './FulfilmentChoice'
import styles from './Orders.module.css'

/** Review the cart and place the order. Only this button places an order (ADR 0019). */
function CheckoutPage() {
  const { cart, refresh } = useCart()
  const navigate = useNavigate()
  const [fulfilment, setFulfilment] = useState<Fulfilment>('pickup')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conflict, setConflict] = useState<string | null>(null)

  async function place(acceptConflicts: boolean) {
    setBusy(true)
    setError(null)
    try {
      const order = await api.placeOrder(fulfilment, acceptConflicts)
      await refresh()
      void navigate(`/orders/${order.id}`)
    } catch (err) {
      if (err instanceof ApiError && err.detail?.code === 'conflict') setConflict(err.message)
      else setError(err instanceof ApiError ? err.message : 'Could not place the order.')
      setBusy(false)
    }
  }

  if (!cart) return null
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
        <div className={styles.confirm} role="alertdialog" aria-label="Please confirm">
          <p>{conflict} Place the order anyway?</p>
          <button type="button" onClick={() => setConflict(null)}>
            Go back
          </button>{' '}
          <button
            className={styles.danger}
            type="button"
            disabled={busy}
            onClick={() => void place(true)}
          >
            Place it anyway
          </button>
        </div>
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
        onClick={() => void place(false)}
      >
        Place order · {cart.total_sar} SAR
      </button>
    </main>
  )
}

export default CheckoutPage
