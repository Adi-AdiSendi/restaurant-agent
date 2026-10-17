import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { mockFetch } from '../../test/fetchMock'
import ChatPanel from './ChatPanel'

const started = { 'POST /api/conversations': { status: 201, body: { id: 1 } } }

function panel(restaurant: string) {
  return (
    <ChatPanel
      restaurant={restaurant}
      username="sara"
      isNew={false}
      onUnauthorized={vi.fn()}
      onReplied={vi.fn()}
    />
  )
}

function conversationStarts(fetchMock: ReturnType<typeof mockFetch>) {
  return fetchMock.mock.calls
    .filter(([url]) => String(url) === '/api/conversations')
    .map(([, init]) => init?.body)
}

describe('ChatPanel restaurants', () => {
  test('a chat starts at its restaurant, and another restaurant starts a new one', async () => {
    const fetchMock = mockFetch(started)
    const { rerender } = render(panel('golden-dragon'))
    await vi.waitFor(() =>
      expect(conversationStarts(fetchMock)).toEqual([
        JSON.stringify({ restaurant: 'golden-dragon' }),
      ]),
    )
    rerender(panel('corner-table'))
    await vi.waitFor(() =>
      expect(conversationStarts(fetchMock)).toEqual([
        JSON.stringify({ restaurant: 'golden-dragon' }),
        JSON.stringify({ restaurant: 'corner-table' }),
      ]),
    )
  })

  test('a slow start for an earlier restaurant never replaces a later one', async () => {
    const pending: ((id: number) => void)[] = []
    const sent = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input) !== '/api/conversations') {
        return Promise.resolve(new Response(JSON.stringify(init?.body ?? null), { status: 500 }))
      }
      return new Promise<Response>((resolve) => {
        pending.push((id) => resolve(new Response(JSON.stringify({ id }), { status: 201 })))
      })
    })
    vi.stubGlobal('fetch', sent)
    const { rerender } = render(panel('corner-table'))
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    rerender(panel('golden-dragon'))
    await vi.waitFor(() => expect(pending).toHaveLength(2))
    await act(async () => pending[1]?.(22))
    await act(async () => pending[0]?.(11))
    fireEvent.change(screen.getByLabelText('Message'), { target: { value: 'hi' } })
    const sendButton = screen.getByRole('button', { name: 'Send' })
    await vi.waitFor(() => expect(sendButton).toBeEnabled())
    fireEvent.click(sendButton)
    await vi.waitFor(() =>
      expect(sent).toHaveBeenCalledWith(
        '/api/chat',
        expect.objectContaining({ body: JSON.stringify({ conversation_id: 22, message: 'hi' }) }),
      ),
    )
  })
})
