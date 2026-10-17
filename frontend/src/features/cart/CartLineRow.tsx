import { useState } from 'react'

import { api, ApiError } from '../../api/client'
import { MAX_QUANTITY, type CartLine } from '../../api/cartTypes'
import { useCart } from './cartContext'
import styles from './CartLineRow.module.css'

interface Props {
  line: CartLine
  /** Checkout shows lines without the quantity and remove buttons. */
  readOnly?: boolean
}

/** One cart line, priced and checked by the server. */
function CartLineRow({ line, readOnly = false }: Props) {
  const { setCart } = useCart()
  const [error, setError] = useState<string | null>(null)

  async function change(call: () => Promise<Parameters<typeof setCart>[0]>) {
    setError(null)
    try {
      setCart(await call())
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not change the cart.')
    }
  }

  const details = [...line.options.map((o) => o.name), ...line.removed.map((r) => `no ${r}`)].join(
    ', ',
  )
  return (
    <li className={styles.line}>
      <div className={styles.top}>
        <span className={styles.name}>
          {readOnly && `${line.quantity} × `}
          {line.name}
        </span>
        <span className={styles.price}>
          {line.line_total_sar ? `${line.line_total_sar} SAR` : 'unavailable'}
        </span>
      </div>
      {details && <p className={styles.details}>{details}</p>}
      <p className={styles.details}>
        Allergens:{' '}
        {line.allergens.length ? line.allergens.join(', ').replaceAll('_', ' ') : 'none listed'}
      </p>
      {line.conflicts_with_guest.length > 0 && (
        <p className={styles.conflict}>
          Not suitable for you: {line.conflicts_with_guest.join(', ')}
        </p>
      )}
      {line.may_contain_warnings.length > 0 && (
        <p className={styles.trace}>
          May contain {line.may_contain_warnings.join(', ').replaceAll('_', ' ')}. Check with staff.
        </p>
      )}
      {line.problem && <p className={styles.conflict}>{line.problem}</p>}
      {!readOnly && (
        <div className={styles.actions}>
          <button
            type="button"
            aria-label={`One less ${line.name}`}
            disabled={line.quantity <= 1}
            onClick={() => void change(() => api.setQuantity(line.id, line.quantity - 1))}
          >
            −
          </button>
          <span aria-label="Quantity">{line.quantity}</span>
          <button
            type="button"
            aria-label={`One more ${line.name}`}
            disabled={line.quantity >= MAX_QUANTITY}
            onClick={() => void change(() => api.setQuantity(line.id, line.quantity + 1))}
          >
            +
          </button>
          <button
            className={styles.remove}
            type="button"
            onClick={() => void change(() => api.removeCartLine(line.id))}
          >
            Remove
          </button>
        </div>
      )}
      {error && (
        <p className={styles.conflict} role="alert">
          {error}
        </p>
      )}
    </li>
  )
}

export default CartLineRow
