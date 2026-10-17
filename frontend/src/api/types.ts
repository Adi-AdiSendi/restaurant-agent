// Mirrors the backend Pydantic models. Keep in sync with app/agent/schemas.py,
// app/tools/menu_views.py, app/menu/restaurant_schemas.py, app/memory/profile.py,
// app/api/auth.py and app/api/health.py.

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
  option_groups: OptionGroup[]
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
}

export interface ChatReply {
  reply: string
  items: Card[]
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

export type PreferenceKind = 'allergy' | 'diet' | 'dislike' | 'like' | 'budget' | 'spice'

export interface Preference {
  id: number
  kind: PreferenceKind
  value: string
  status: 'active' | 'superseded' | 'removed'
  is_hard: boolean
  superseded_by: number | null
  created_at: string
}
