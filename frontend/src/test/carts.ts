// Cart payloads for UI tests.
import type { Cart } from '../api/cartTypes'

export const emptyCart: Cart = { restaurant: null, lines: [], total_sar: '0', item_count: 0 }

export const cartRoute = { 'GET /api/cart': { body: emptyCart } }
