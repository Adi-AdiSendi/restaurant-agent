import { useCallback, useEffect, useReducer, useRef } from 'react'

import { api, ApiError } from '../../api/client'
import { chatReducer, initialChat } from './chatReducer'

interface Options {
  onUnauthorized: () => void
  onReplied: () => void
}

const FALLBACK = 'Something went wrong. Please try again.'

export function useChat({ onUnauthorized, onReplied }: Options) {
  const [state, dispatch] = useReducer(chatReducer, initialChat)
  const started = useRef(false)

  const newChat = useCallback(async () => {
    try {
      const { id } = await api.newConversation()
      dispatch({ type: 'started', conversationId: id })
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized()
      else
        dispatch({ type: 'startFailed', error: err instanceof ApiError ? err.message : FALLBACK })
    }
  }, [onUnauthorized])

  useEffect(() => {
    // StrictMode runs effects twice in development; start only one conversation.
    if (started.current) return
    started.current = true
    void newChat()
  }, [newChat])

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || state.conversationId === null || state.sending) return
      dispatch({ type: 'sent', text: trimmed })
      try {
        const reply = await api.sendMessage(state.conversationId, trimmed)
        dispatch({ type: 'replied', reply })
        onReplied()
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          onUnauthorized()
          return
        }
        const status = err instanceof ApiError ? err.status : 0
        dispatch({
          type: 'failed',
          status,
          error: err instanceof ApiError ? err.message : FALLBACK,
        })
      }
    },
    [state.conversationId, state.sending, onUnauthorized, onReplied],
  )

  const retry = useCallback(() => {
    if (state.retry === 'send' && state.failedText) void send(state.failedText)
    else if (state.retry === 'start') void newChat()
  }, [state.retry, state.failedText, send, newChat])

  return { state, send, retry, newChat }
}
