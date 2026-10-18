// Menu payloads. Keep in sync with app/menu/guest_view.py and
// app/menu/restaurant_schemas.py.

export type Allergen =
  | 'gluten'
  | 'dairy'
  | 'egg'
  | 'peanut'
  | 'tree_nut'
  | 'soy'
  | 'sesame'
  | 'fish'
  | 'shellfish'
  | 'mustard'

export interface CardOption {
  id: number
  name: string
  price_delta_sar: string
  allergens: Allergen[]
  may_contain: Allergen[]
  is_vegetarian: boolean
  is_vegan: boolean
  spice_level: number
  /** Why this guest must not pick it (saved allergies or diet); empty if they may. */
  conflicts_with_guest: string[]
  /** Trace allergens of this option that the guest avoids. */
  may_contain_warnings: Allergen[]
}

export interface OptionGroup {
  id: number
  name: string
  min_choices: number
  max_choices: number
  options: CardOption[]
}

export interface Card {
  id: number
  name: string
  /** One of the restaurant's own category slugs. */
  category: string
  description: string
  price_sar: string
  is_vegetarian: boolean
  is_vegan: boolean
  spice_level: number
  ingredients: string[]
  allergens: Allergen[]
  may_contain: Allergen[]
  removable: string[]
  /** A similar dish's photo, `<restaurant>/<name>`; null shows a category icon. */
  photo: string | null
  option_groups: OptionGroup[]
  /** Why no way of ordering it suits the guest; empty if one does. */
  conflicts_with_guest: string[]
  may_contain_warnings: Allergen[]
}

export interface Restaurant {
  id: number
  slug: string
  name: string
  cuisine: string
  tagline: string
  accent_color: string
  categories: string[]
  /** The cover photo, `<restaurant>/<name>`; null shows the accent colour. */
  photo: string | null
}

export interface GuestMenu {
  restaurant: Restaurant
  /** Every dish, in the restaurant's category order; ones that do not suit the guest say why. */
  items: Card[]
}
