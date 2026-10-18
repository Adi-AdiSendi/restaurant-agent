import type { ChatAction, ChatMessage, ChatState } from './chatTypes'

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
    case 'starting':
      // The old chat goes away and nothing can be sent until the new one exists.
      return { ...initialChat, nextId: state.nextId }
    case 'started':
      return { ...initialChat, conversationId: action.conversationId, nextId: state.nextId }
    case 'sent':
      return {
        ...withMessage(state, { role: 'user', text: action.text, items: [], actions: [] }),
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
          actions: action.reply.actions,
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
