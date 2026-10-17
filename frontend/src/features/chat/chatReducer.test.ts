import { describe, expect, test } from 'vitest'

import type { ChatReply } from '../../api/types'
import { chatReducer, initialChat, type ChatState } from './chatReducer'

const started: ChatState = chatReducer(initialChat, { type: 'started', conversationId: 7 })
const reply: ChatReply = { reply: 'Try the bowl', items: [] }

describe('chatReducer', () => {
  test('a sent message shows at once and marks the chat as sending', () => {
    const state = chatReducer(started, { type: 'sent', text: 'hi' })
    expect(state.messages.map((m) => [m.role, m.text])).toEqual([['user', 'hi']])
    expect(state.sending).toBe(true)
  })

  test('a reply is appended and sending stops', () => {
    const sent = chatReducer(started, { type: 'sent', text: 'hi' })
    const state = chatReducer(sent, { type: 'replied', reply })
    expect(state.messages.map((m) => m.role)).toEqual(['user', 'assistant'])
    expect(state.sending).toBe(false)
  })

  test('a failure removes the unanswered message and keeps it for retry', () => {
    const sent = chatReducer(started, { type: 'sent', text: 'hi' })
    const state = chatReducer(sent, {
      type: 'failed',
      error: 'The assistant is unavailable.',
      status: 503,
    })
    expect(state.messages).toEqual([])
    expect(state.failedText).toBe('hi')
    expect(state.error).toBe('The assistant is unavailable.')
  })

  test('only network and gateway errors can be resent', () => {
    const sent = chatReducer(started, { type: 'sent', text: 'hi' })
    for (const status of [0, 502, 503, 504]) {
      expect(chatReducer(sent, { type: 'failed', error: 'x', status }).retry).toBe('send')
    }
    for (const status of [404, 422, 500]) {
      expect(chatReducer(sent, { type: 'failed', error: 'x', status }).retry).toBeNull()
    }
    expect(chatReducer(started, { type: 'startFailed', error: 'x' }).retry).toBe('start')
  })

  test('sending again clears the error', () => {
    const failed = chatReducer(chatReducer(started, { type: 'sent', text: 'hi' }), {
      type: 'failed',
      error: 'x',
      status: 502,
    })
    const state = chatReducer(failed, { type: 'sent', text: 'hi' })
    expect(state.error).toBeNull()
    expect(state.failedText).toBeNull()
  })

  test('a new conversation starts empty with unique message ids', () => {
    const chatted = chatReducer(chatReducer(started, { type: 'sent', text: 'a' }), {
      type: 'replied',
      reply,
    })
    const fresh = chatReducer(chatted, { type: 'started', conversationId: 8 })
    expect(fresh.conversationId).toBe(8)
    expect(fresh.messages).toEqual([])
    expect(fresh.nextId).toBe(chatted.nextId)
  })

  test('starting a chat clears the old one and blocks sending until it exists', () => {
    const chatting = chatReducer(chatReducer(initialChat, { type: 'started', conversationId: 4 }), {
      type: 'sent',
      text: 'hi',
    })
    const next = chatReducer(chatting, { type: 'starting' })
    expect(next.conversationId).toBeNull()
    expect(next.messages).toEqual([])
    expect(next.nextId).toBe(chatting.nextId)
  })
})
