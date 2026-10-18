// Chat reply builders for UI tests. Shapes mirror the backend ChatReply.
import type { CartAction, ChatReply } from '../api/types'
import { emptyCart, latteCart, oatLatte } from './carts'

export function chatReply(reply: string, extra: Partial<ChatReply> = {}): ChatReply {
  return { reply, items: [], actions: [], cart: emptyCart, ...extra }
}

export const addedLatte: CartAction = {
  kind: 'added',
  quantity: 2,
  line: oatLatte,
  left_out: ['sugar'],
}

export const checkout: CartAction = { kind: 'checkout', quantity: 0, line: null, left_out: [] }

/** A reply that added two oat lattes; the cart it carries holds them. */
export const latteAdded = chatReply('Added two lattes.', { actions: [addedLatte], cart: latteCart })
