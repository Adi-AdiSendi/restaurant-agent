import { createContext, useContext } from 'react'

import type { Cart } from '../../api/cartTypes'

export interface CartState {
  /** The server's cart; null until it has loaded. */
  cart: Cart | null
  /** Show a cart the server just returned (every cart call returns the whole cart). */
  setCart: (cart: Cart) => void
  refresh: () => Promise<void>
}

export const CartContext = createContext<CartState | null>(null)

export function useCart(): CartState {
  const state = useContext(CartContext)
  if (!state) throw new Error('useCart must be used inside CartProvider')
  return state
}
