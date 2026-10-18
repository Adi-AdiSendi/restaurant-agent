// Mirrors the backend Pydantic models. Keep in sync with app/agent/schemas.py,
// app/agent/turn_reply.py, app/memory/profile.py, app/api/preferences.py,
// app/api/auth.py and app/api/health.py. Menu types are in menuTypes.ts, cart types in cartTypes.ts.
import type { Cart, CartLine } from './cartTypes'
import type { Card } from './menuTypes'

/** A cart change the chat made, from the server's tool result; or a checkout card. */
export interface CartAction {
  kind: 'added' | 'updated' | 'removed' | 'cleared' | 'checkout'
  quantity: number
  /** The line as it is now (as it was, for a removal); null for checkout. */
  line: CartLine | null
  /** Ingredients left out because the guest dislikes them. */
  left_out: string[]
}

/** A category the guest asked to see: every dish, unsuitable ones marked. Not a recommendation. */
export interface MenuBlock {
  category: string
  items: Card[]
}

export interface ChatReply {
  reply: string
  items: Card[]
  actions: CartAction[]
  /** The cart as it is after this turn. */
  cart: Cart
  menus: MenuBlock[]
}

export interface LoginResponse {
  username: string
  is_new: boolean
}

export interface Me {
  username: string
}

export interface Health {
  status: string
}

export interface NewConversation {
  id: number
}

// backend/tests/test_chat_parity.py checks this list against the backend's kinds.
export type PreferenceKind =
  | 'allergy'
  | 'diet'
  | 'dislike'
  | 'like'
  | 'budget'
  | 'spice'
  | 'day_dislike'
  | 'day_like'
  | 'calories'

/** The values each kind accepts, from the server (the page keeps no copy). */
export interface PreferenceVocabulary {
  allergens: string[]
  diets: string[]
  spice_levels: string[]
  weekdays: string[]
  calories_min: number
  calories_max: number
}

/** Today in Riyadh, and the estimated kcal the guest ordered today. */
export interface Today {
  weekday: string
  kcal: number
}

export interface Preference {
  id: number
  kind: PreferenceKind
  value: string
  status: 'active' | 'superseded' | 'removed'
  is_hard: boolean
  superseded_by: number | null
  created_at: string
}
