import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import type { Fulfilment } from '../../api/cartTypes'
import { useCart } from '../cart/cartContext'
import CartLineRow from '../cart/CartLineRow'
import FulfilmentChoice from './FulfilmentChoice'
import PlaceConfirm from './PlaceConfirm'
import styles from './Orders.module.css'
import { usePlaceOrder } from './usePlaceOrder'

/** Review the cart and place the order. Only the guest's button places an order, here or on
 * a chat checkout card (ADR 0019). */
function CheckoutPage() {
  const { cart, error: loadError, refresh } = useCart()
  const [fulfilment, setFulfilment] = useState<Fulfilment>('pickup')
  const { busy, error, conflict, place, back } = usePlaceOrder(fulfilment)

  useEffect(() => {
    void refresh()
  }, [refresh])

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
          onBack={back}
          onPlace={() => place(conflict.reasons)}
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
        onClick={() => place([])}
      >
        Place order · {cart.total_sar} SAR
      </button>
    </main>
  )
}

export default CheckoutPage
