// Cart payloads for UI tests.
import type { Cart, CartLine, Order } from '../api/cartTypes'

export const emptyCart: Cart = {
  restaurant: null,
  lines: [],
  total_sar: '0',
  item_count: 0,
  kcal: 0,
}

export const cartRoute = { 'GET /api/cart': { body: emptyCart } }

export const oatLatte: CartLine = {
  id: 9,
  item_id: 40,
  name: 'Latte',
  quantity: 2,
  options: [{ id: 2, name: 'Oat milk', price_delta_sar: '3.00' }],
  removed: ['sugar'],
  unit_price_sar: '19.00',
  line_total_sar: '38.00',
  kcal: 170,
  allergens: [],
  conflicts_with_guest: [],
  may_contain_warnings: [],
  problem: null,
}

export const latteCart: Cart = {
  restaurant: { slug: 'bean-and-bloom', name: 'Bean & Bloom' },
  lines: [oatLatte],
  total_sar: '38.00',
  item_count: 2,
  kcal: 340,
}

export const placedOrder: Order = {
  id: 31,
  restaurant: { slug: 'bean-and-bloom', name: 'Bean & Bloom' },
  fulfilment: 'pickup',
  total_sar: '38.00',
  item_count: 2,
  placed_at: '2026-10-17T18:00:00Z',
  status: 'preparing',
  photos: ['bean-and-bloom/latte'],
  kcal: 340,
  lines: [
    {
      item_name: 'Latte',
      quantity: 2,
      unit_price_sar: '19.00',
      option_names: ['Oat milk'],
      removed: ['sugar'],
      allergens: [],
      kcal: 170,
      photo: 'bean-and-bloom/latte',
    },
  ],
}
