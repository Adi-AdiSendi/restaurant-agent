import { useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Card } from '../../api/menuTypes'
import { useCart } from '../cart/cartContext'
import type { Choice } from './choice'

/** What the server asked before adding: consent to a conflict, or to replacing the cart. */
export type Ask =
  | { kind: 'conflict'; message: string; reasons: string[] }
  | { kind: 'other_restaurant'; restaurant: string }

interface Consent {
  /** The exact choice the guest answered for; any change asks again. */
  choice: Choice
  accepted_reasons: string[]
  replace_cart: boolean
}

interface Options {
  item: Card
  restaurant: string
  choice: Choice
  onAdded: () => void
  onUnauthorized: () => void
}

const NONE = { accepted_reasons: [] as string[], replace_cart: false }

/** Add a configured dish. A 409 becomes a question; the answer resends with consent
 * that names what the guest saw, so the server refuses any other conflict. */
export function useAddLine({ item, restaurant, choice, onAdded, onUnauthorized }: Options) {
  const { setCart } = useCart()
  const [ask, setAsk] = useState<Ask | null>(null)
  const [consent, setConsent] = useState<Consent | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const current = consent?.choice === choice ? consent : { choice, ...NONE }

  async function send(given: Consent) {
    setBusy(true)
    setError(null)
    try {
      const { accepted_reasons, replace_cart } = given
      const line = { item_id: item.id, option_ids: choice.optionIds, removed: choice.removed }
      const body = {
        restaurant,
        quantity: choice.quantity,
        ...line,
        accepted_reasons,
        replace_cart,
      }
      setCart(await api.addCartLine(body))
      onAdded()
    } catch (err) {
      const detail = err instanceof ApiError ? err.detail : null
      if (err instanceof ApiError && err.status === 401) onUnauthorized()
      else if (err instanceof ApiError && detail?.code === 'conflict') {
        setAsk({ kind: 'conflict', message: err.message, reasons: detail.reasons ?? [] })
      } else if (detail?.code === 'other_restaurant') {
        setAsk({ kind: 'other_restaurant', restaurant: detail.restaurant ?? 'another restaurant' })
      } else setError(err instanceof ApiError ? err.message : 'Could not add it. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  function confirm() {
    if (!ask) return
    const given: Consent =
      ask.kind === 'conflict'
        ? { ...current, accepted_reasons: ask.reasons }
        : { ...current, replace_cart: true }
    setConsent(given)
    setAsk(null)
    void send(given)
  }

  return {
    ask,
    busy,
    error,
    submit: () => void send(current),
    confirm,
    cancel: () => setAsk(null),
  }
}
