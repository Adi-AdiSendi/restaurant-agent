import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, ApiError } from '../../api/client'
import type { Cart } from '../../api/cartTypes'
import { CartContext } from './cartContext'

interface Props {
  children: ReactNode
  onUnauthorized: () => void
}

/** Holds the server's cart for every page. The server is the only source of truth, so
 * pages refresh it whenever something else may have changed it (a chat reply, checkout). */
function CartProvider({ children, onUnauthorized }: Props) {
  const [cart, setCart] = useState<Cart | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(
    () =>
      api.cart().then(
        (loaded) => {
          setCart(loaded)
          setError(null)
        },
        (err: unknown) => {
          if (err instanceof ApiError && err.status === 401) onUnauthorized()
          else setError(err instanceof ApiError ? err.message : 'Could not load your cart.')
        },
      ),
    [onUnauthorized],
  )

  useEffect(() => {
    void refresh()
  }, [refresh])

  const value = useMemo(() => ({ cart, error, setCart, refresh }), [cart, error, refresh])
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export default CartProvider
