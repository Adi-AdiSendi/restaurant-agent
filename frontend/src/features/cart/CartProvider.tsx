import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { api, ApiError } from '../../api/client'
import type { Cart } from '../../api/cartTypes'
import { CartContext } from './cartContext'

interface Props {
  children: ReactNode
  onUnauthorized: () => void
}

/** Holds the server's cart for every page. The server is the only source of truth. */
function CartProvider({ children, onUnauthorized }: Props) {
  const [cart, setCart] = useState<Cart | null>(null)

  const refresh = useCallback(
    () =>
      api.cart().then(setCart, (err: unknown) => {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
      }),
    [onUnauthorized],
  )

  useEffect(() => {
    void refresh()
  }, [refresh])

  const value = useMemo(() => ({ cart, setCart, refresh }), [cart, refresh])
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export default CartProvider
