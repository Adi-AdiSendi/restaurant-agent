import { useState } from 'react'
import { Link } from 'react-router'

import { api, ApiError } from '../../api/client'
import { kcalLabel } from '../../components/kcal'
import { useModal } from '../../components/useModal'
import { useCart } from './cartContext'
import styles from './CartDrawer.module.css'
import CartLineRow from './CartLineRow'

interface Props {
  onClose: () => void
}

/** The cart, from the side (or the bottom on a phone). Checkout is a separate page. */
function CartDrawer({ onClose }: Props) {
  const { cart, error: loadError, setCart, refresh } = useCart()
  const dialog = useModal<HTMLElement>(onClose)
  const [error, setError] = useState<string | null>(null)
  const lines = cart?.lines ?? []
  const blocked = lines.some((l) => l.problem !== null)

  async function clear() {
    try {
      setCart(await api.clearCart())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not clear the cart.')
    }
  }

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <aside
        ref={dialog}
        className={styles.drawer}
        role="dialog"
        aria-modal="true"
        aria-label="Your cart"
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.head}>
          <h2 className={styles.title}>
            Your cart{cart?.restaurant ? ` · ${cart.restaurant.name}` : ''}
          </h2>
          <button className={styles.close} type="button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        {lines.length === 0 ? (
          <p className={styles.empty}>
            Your cart is empty. Pick a dish from a menu, or ask the assistant.
          </p>
        ) : (
          <ul className={styles.lines}>
            {lines.map((line) => (
              <CartLineRow key={line.id} line={line} />
            ))}
          </ul>
        )}
        {(error ?? loadError) && (
          <p role="alert">
            {error ?? loadError}{' '}
            <button type="button" onClick={() => void refresh()}>
              Retry
            </button>
          </p>
        )}
        {lines.length > 0 && (
          <footer className={styles.foot}>
            <div className={styles.total}>
              <span>Total</span>
              <span>{cart?.total_sar} SAR</span>
            </div>
            {cart?.kcal ? <p className={styles.blocked}>{kcalLabel(cart.kcal)}</p> : null}
            {blocked && (
              <p className={styles.blocked}>Remove the unavailable dishes to check out.</p>
            )}
            <div className={styles.buttons}>
              <button className={styles.secondary} type="button" onClick={() => void clear()}>
                Empty cart
              </button>
              {blocked ? (
                <span className={styles.checkoutOff}>Checkout</span>
              ) : (
                <Link className={styles.checkout} to="/checkout" onClick={onClose}>
                  Checkout
                </Link>
              )}
            </div>
          </footer>
        )}
      </aside>
    </div>
  )
}

export default CartDrawer
