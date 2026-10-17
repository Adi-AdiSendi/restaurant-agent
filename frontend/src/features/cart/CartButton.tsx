import { useState } from 'react'

import { useCart } from './cartContext'
import styles from './CartButton.module.css'
import CartDrawer from './CartDrawer'

/** The header's cart button, with the item count, and the drawer it opens. */
function CartButton() {
  const { cart } = useCart()
  const [open, setOpen] = useState(false)
  const count = cart?.item_count ?? 0
  return (
    <>
      <button className={styles.button} type="button" onClick={() => setOpen(true)}>
        Cart{count > 0 && <span className={styles.count}>{count}</span>}
      </button>
      {open && <CartDrawer onClose={() => setOpen(false)} />}
    </>
  )
}

export default CartButton
