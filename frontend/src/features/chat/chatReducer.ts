import type { Card, ChatReply } from '../../api/types'

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
  items: Card[]
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
  | { type: 'started'; conversationId: number }
  | { type: 'sent'; text: string }
  | { type: 'replied'; reply: ChatReply }
  | { type: 'failed'; error: string; status: number }
  | { type: 'startFailed'; error: string }

export const initialChat: ChatState = {
  conversationId: null,
  messages: [],
  sending: false,
  error: null,
  retry: null,
  failedText: null,
  nextId: 1,
}

// 504: the turn hit its deadline and was rolled back, so resending is safe.
const RETRYABLE = new Set([0, 502, 503, 504])

function withMessage(state: ChatState, message: Omit<ChatMessage, 'id'>): ChatState {
  return {
    ...state,
    messages: [...state.messages, { ...message, id: state.nextId }],
    nextId: state.nextId + 1,
  }
}

export function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'started':
      return { ...initialChat, conversationId: action.conversationId, nextId: state.nextId }
    case 'sent':
      return {
        ...withMessage(state, { role: 'user', text: action.text, items: [] }),
        sending: true,
        error: null,
        retry: null,
        failedText: null,
      }
    case 'replied':
      return {
        ...withMessage(state, {
          role: 'assistant',
          text: action.reply.reply,
          items: action.reply.items,
        }),
        sending: false,
      }
    case 'failed': {
      // Drop the unanswered user bubble; Retry sends it again.
      const last = state.messages.at(-1)
      const unanswered = last?.role === 'user' ? last : undefined
      return {
        ...state,
        messages: unanswered ? state.messages.slice(0, -1) : state.messages,
        sending: false,
        error: action.error,
        retry: unanswered && RETRYABLE.has(action.status) ? 'send' : null,
        failedText: unanswered?.text ?? null,
      }
    }
    case 'startFailed':
      return { ...state, sending: false, error: action.error, retry: 'start', failedText: null }
  }
}
