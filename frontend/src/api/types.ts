// Mirrors the backend Pydantic models. Keep in sync with app/agent/schemas.py,
// app/memory/profile.py, app/api/auth.py and app/api/health.py. Menu types are
// in menuTypes.ts.
import type { Card } from './menuTypes'

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
