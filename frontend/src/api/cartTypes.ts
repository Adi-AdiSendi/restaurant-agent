// Cart and order payloads. Keep in sync with app/orders/schemas.py and
// app/api/cart.py, app/api/orders.py. Prices arrive as strings ("19.00").
import type { Allergen } from './menuTypes'

/** Most of one dish in a cart line; the server has the same limit. */
export const MAX_QUANTITY = 20

export interface AddLine {
  restaurant: string
  item_id: number
  quantity: number
  option_ids: number[]
  removed: string[]
  /** The conflict reasons the guest was shown and accepted; any other conflict asks again. */
  accepted_reasons: string[]
  /** The guest agreed to empty a cart from another restaurant. */
  replace_cart: boolean
}

export interface CartLineOption {
  id: number
  name: string
  price_delta_sar: string
}

export interface CartLine {
  id: number
  item_id: number
  name: string
  quantity: number
  options: CartLineOption[]
  removed: string[]
  unit_price_sar: string | null
  line_total_sar: string | null
  /** Estimated kcal of one, with its options. */
  kcal: number | null
  allergens: Allergen[]
  conflicts_with_guest: string[]
  may_contain_warnings: Allergen[]
  /** Why the line cannot be ordered any more (the menu changed); null if it can. */
  problem: string | null
}

export interface CartRestaurant {
  slug: string
  name: string
}

export interface Cart {
  restaurant: CartRestaurant | null
  lines: CartLine[]
  total_sar: string
  item_count: number
  /** Estimated kcal of the whole cart. */
  kcal: number
}

export type Fulfilment = 'pickup' | 'dine_in'
export type OrderStatus = 'placed' | 'preparing' | 'ready'

export interface OrderLine {
  item_name: string
  quantity: number
  unit_price_sar: string
  option_names: string[]
  removed: string[]
  allergens: Allergen[]
  kcal: number | null
  /** The dish's photo today; null if it has none or left the menu. */
  photo: string | null
}

export interface OrderSummary {
  id: number
  restaurant: CartRestaurant
  fulfilment: Fulfilment
  total_sar: string
  item_count: number
  placed_at: string
  status: OrderStatus
  /** Photos of the dishes in the order, at most 4. */
  photos: string[]
  /** Estimated kcal of the whole order. */
  kcal: number | null
}

export interface Order extends OrderSummary {
  lines: OrderLine[]
}
