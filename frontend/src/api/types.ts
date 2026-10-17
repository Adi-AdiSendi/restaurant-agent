// Mirrors the backend Pydantic models. Keep in sync with app/agent/schemas.py,
// app/menu/schemas.py, app/memory/profile.py, app/api/auth.py and app/api/health.py.

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

export type Category = 'starters' | 'burgers_and_mains' | 'bowls_and_pasta' | 'desserts_and_drinks'

export interface Card {
  id: number
  name: string
  category: Category
  description: string
  price_sar: string
  is_vegetarian: boolean
  is_vegan: boolean
  spice_level: number
  ingredients: string[]
  allergens: Allergen[]
  may_contain: Allergen[]
  may_contain_warnings: Allergen[]
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
