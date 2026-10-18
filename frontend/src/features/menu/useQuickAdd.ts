import { useCallback, useEffect, useState } from 'react'

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

  useEffect(() => {
    if (added === null) return
    const timer = setTimeout(() => setAdded(null), ADDED_MS)
    return () => clearTimeout(timer)
  }, [added])

  const send = useCallback(
    async (item: Card) => {
      const line = { item_id: item.id, quantity: 1, option_ids: [], removed: [] }
      try {
        const body = { restaurant, ...line, accepted_reasons: [], replace_cart: false }
        setCart(await api.addCartLine(body))
        setAdded(item.id)
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        else onNeedsSheet(item)
      }
    },
    [restaurant, setCart, onNeedsSheet, onUnauthorized],
  )

  const add = useCallback((item: Card) => void send(item), [send])
  return { add, added }
}
