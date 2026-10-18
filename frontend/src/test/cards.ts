// Card and option builders for UI tests. Shapes mirror the backend GuestItem.
import type { Card, CardOption } from '../api/menuTypes'

export function option(id: number, name: string, extra: Partial<CardOption> = {}): CardOption {
  return {
    id,
    name,
    price_delta_sar: '0.00',
    allergens: [],
    may_contain: [],
    is_vegetarian: true,
    is_vegan: true,
    spice_level: 0,
    kcal_delta: 0,
    conflicts_with_guest: [],
    may_contain_warnings: [],
    ...extra,
  }
}

/** A latte: one required milk (whole conflicts with the guest) and up to two syrups. */
export const latte: Card = {
  id: 40,
  name: 'Latte',
  category: 'coffee',
  description: 'Espresso with steamed milk.',
  price_sar: '16.00',
  is_vegetarian: true,
  is_vegan: true,
  spice_level: 0,
  ingredients: ['espresso', 'sugar'],
  allergens: [],
  may_contain: [],
  removable: ['sugar'],
  photo: null,
  kcal: 150,
  pack_size: 1,
  pack_unit: null,
  option_groups: [
    {
      id: 7,
      name: 'Milk',
      min_choices: 1,
      max_choices: 1,
      options: [
        option(1, 'Whole milk', { allergens: ['dairy'], conflicts_with_guest: ['dairy'] }),
        option(2, 'Oat milk', { price_delta_sar: '3.00', may_contain_warnings: ['gluten'] }),
      ],
    },
    {
      id: 8,
      name: 'Syrup',
      min_choices: 0,
      max_choices: 2,
      options: [
        option(3, 'Vanilla', { price_delta_sar: '2.00' }),
        option(4, 'Caramel', { price_delta_sar: '2.00' }),
        option(5, 'Chilli', { spice_level: 3 }),
      ],
    },
  ],
  conflicts_with_guest: [],
  may_contain_warnings: [],
  taste_notes: [],
  liked: false,
}
