import type { Card } from '../../api/menuTypes'
import type { CartAction, ChatReply, MenuBlock } from '../../api/types'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  items: Card[]
  /** Cart changes this reply made, and a checkout card if one was proposed. */
  actions: CartAction[]
  /** Categories the guest asked to see. */
  menus: MenuBlock[]
}

/** What Retry should do, or null when retrying cannot help (e.g. 404, 422). */
export type RetryAction = 'send' | 'start' | null

export interface ChatState {
  conversationId: number | null
  messages: ChatMessage[]
  sending: boolean
  error: string | null
  retry: RetryAction
  /** The message that failed, kept so Retry can resend it. */
  failedText: string | null
  nextId: number
}

export type ChatAction =
  | { type: 'starting' }
  | { type: 'started'; conversationId: number }
  | { type: 'sent'; text: string }
  | { type: 'replied'; reply: ChatReply }
  | { type: 'failed'; error: string; status: number }
  | { type: 'startFailed'; error: string }
