import { useState } from 'react'

import type { Fulfilment } from '../../api/cartTypes'
import { useCart } from '../cart/cartContext'
import FulfilmentChoice from './FulfilmentChoice'
import PlaceConfirm from './PlaceConfirm'
import styles from './Orders.module.css'
import { usePlaceOrder } from './usePlaceOrder'

/** The checkout the assistant proposed, under its reply. It shows the cart as it is now,
 * and only the guest's button places the order (ADR 0019). */
function CheckoutCard() {
  const { cart } = useCart()
  const [fulfilment, setFulfilment] = useState<Fulfilment>('pickup')
  const { busy, error, conflict, place, back } = usePlaceOrder(fulfilment)

  if (!cart) return null
  if (cart.lines.length === 0) {
    return (
      <section className={styles.card} aria-label="Checkout">
        <p className={styles.note}>Your cart is empty.</p>
      </section>
    )
  }
  const blocked = cart.lines.some((line) => line.problem !== null)
  const items = cart.item_count === 1 ? '1 item' : `${cart.item_count} items`
  return (
    <section className={styles.card} aria-label="Checkout">
      <p>
        <strong>{cart.restaurant?.name}</strong> · {items} · {cart.total_sar} SAR
      </p>
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
      {blocked ? (
        <p className={styles.note}>Remove the unavailable dishes in your cart to check out.</p>
      ) : (
        <button
          className={styles.place}
          type="button"
          disabled={busy || conflict !== null}
          onClick={() => place([])}
        >
          Place order · {cart.total_sar} SAR
        </button>
      )}
    </section>
  )
}

export default CheckoutCard
