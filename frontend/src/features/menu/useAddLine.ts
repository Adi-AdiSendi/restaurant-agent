import { useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Card } from '../../api/menuTypes'
import { useCart } from '../cart/cartContext'
import type { Choice } from './choice'

/** What the server asked before adding: consent to a conflict, or to replacing the cart. */
export type Ask =
  { kind: 'conflict'; message: string } | { kind: 'other_restaurant'; restaurant: string }

interface Options {
  item: Card
  restaurant: string
  choice: Choice
  onAdded: () => void
  onUnauthorized: () => void
}

/** Add a configured dish. A 409 becomes a question; the answer resends with consent. */
export function useAddLine({ item, restaurant, choice, onAdded, onUnauthorized }: Options) {
  const { setCart } = useCart()
  const [ask, setAsk] = useState<Ask | null>(null)
  const [consent, setConsent] = useState({ accept_conflict: false, replace_cart: false })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function send(given: typeof consent) {
    setBusy(true)
    setError(null)
    try {
      const line = { item_id: item.id, option_ids: choice.optionIds, removed: choice.removed }
      setCart(await api.addCartLine({ restaurant, quantity: choice.quantity, ...line, ...given }))
      onAdded()
    } catch (err) {
      const code = err instanceof ApiError ? err.detail?.code : undefined
      if (err instanceof ApiError && err.status === 401) onUnauthorized()
      else if (err instanceof ApiError && code === 'conflict') {
        setAsk({ kind: 'conflict', message: err.message })
      } else if (err instanceof ApiError && code === 'other_restaurant') {
        setAsk({
          kind: 'other_restaurant',
          restaurant: err.detail?.restaurant ?? 'another restaurant',
        })
      } else setError(err instanceof ApiError ? err.message : 'Could not add it. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  function confirm() {
    if (!ask) return
    const given = {
      ...consent,
      [ask.kind === 'conflict' ? 'accept_conflict' : 'replace_cart']: true,
    }
    setConsent(given)
    setAsk(null)
    void send(given)
  }

  return {
    ask,
    busy,
    error,
    submit: () => void send(consent),
    confirm,
    cancel: () => setAsk(null),
  }
}
