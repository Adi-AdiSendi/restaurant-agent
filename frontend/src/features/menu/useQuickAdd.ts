import { useCallback, useEffect, useRef, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Card } from '../../api/menuTypes'
import { useCart } from '../cart/cartContext'
import type { QuickAdd } from '../chat/quickAdd'

const ADDED_MS = 2_000

interface Options {
  restaurant: string
  /** Opens the item sheet: anything the server asks about (a conflict, another
   * restaurant's cart) is answered there, by the guest. */
  onNeedsSheet: (item: Card) => void
  onUnauthorized: () => void
}

/** Add one dish with its defaults. The server still prices and checks it. */
export function useQuickAdd({ restaurant, onNeedsSheet, onUnauthorized }: Options): QuickAdd {
  const { setCart } = useCart()
  const [added, setAdded] = useState<number | null>(null)
  const [pending, setPending] = useState<number | null>(null)
  // Only the latest add may set the cart, so a slow earlier answer cannot undo a newer one.
  const latest = useRef(0)

  useEffect(() => {
    if (added === null) return
    const timer = setTimeout(() => setAdded(null), ADDED_MS)
    return () => clearTimeout(timer)
  }, [added])

  const send = useCallback(
    async (item: Card) => {
      const request = ++latest.current
      setPending(item.id)
      const line = { item_id: item.id, quantity: 1, option_ids: [], removed: [] }
      try {
        const body = { restaurant, ...line, accepted_reasons: [], replace_cart: false }
        const cart = await api.addCartLine(body)
        if (request !== latest.current) return
        setCart(cart)
        setAdded(item.id)
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        else onNeedsSheet(item)
      } finally {
        if (request === latest.current) setPending(null)
      }
    },
    [restaurant, setCart, onNeedsSheet, onUnauthorized],
  )

  const add = useCallback(
    (item: Card) => {
      if (pending === null) void send(item)
    },
    [pending, send],
  )
  return { add, added, pending }
}
