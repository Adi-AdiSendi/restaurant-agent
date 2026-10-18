import { useState } from 'react'
import { useNavigate } from 'react-router'

import { api, ApiError } from '../../api/client'
import type { Fulfilment } from '../../api/cartTypes'
import { useCart } from '../cart/cartContext'

interface Conflict {
  message: string
  reasons: string[]
}

/** Place the guest's order from their button (ADR 0019), then open it. A conflict with
 * their saved profile becomes a question; the answer resends with those reasons only. */
export function usePlaceOrder(fulfilment: Fulfilment) {
  const { refresh } = useCart()
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conflict, setConflict] = useState<Conflict | null>(null)

  async function place(acceptedReasons: string[]) {
    setBusy(true)
    setError(null)
    try {
      const order = await api.placeOrder(fulfilment, acceptedReasons)
      await refresh()
      void navigate(`/orders/${order.id}`)
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail : null
      if (detail?.code === 'conflict')
        setConflict({ message: detail.message, reasons: detail.reasons ?? [] })
      else setError(err instanceof ApiError ? err.message : 'Could not place the order.')
      void refresh()
      setBusy(false)
    }
  }

  return {
    busy,
    error,
    conflict,
    place: (acceptedReasons: string[]) => void place(acceptedReasons),
    back: () => setConflict(null),
  }
}
