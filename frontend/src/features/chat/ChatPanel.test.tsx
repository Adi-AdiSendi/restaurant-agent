import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { ChatReply } from '../../api/types'
import { mockFetch } from '../../test/fetchMock'
import ChatPanel from './ChatPanel'

const reply: ChatReply = { reply: 'Try the sorbet.', items: [] }
const prefs = { 'GET /api/preferences': { body: [] } }
const started = { 'POST /api/conversations': { status: 201, body: { id: 1 } } }

function renderPage(onLogout = vi.fn()) {
  render(
    <ChatPanel
      restaurant="corner-table"
      username="sara"
      isNew={false}
      onUnauthorized={onLogout}
      onReplied={vi.fn()}
    />,
  )
  return onLogout
}

async function say(text: string) {
  const input = await screen.findByLabelText('Message')
  fireEvent.change(input, { target: { value: text } })
  // Send stays disabled until the conversation has started.
  const sendButton = screen.getByRole('button', { name: 'Send' })
  await vi.waitFor(() => expect(sendButton).toBeEnabled())
  fireEvent.click(sendButton)
}

describe('ChatPanel', () => {
  test('a 503 shows Retry, and Retry resends the same message', async () => {
    const fetchMock = mockFetch({
      ...prefs,
      ...started,
      'POST /api/chat': [
        { status: 503, body: { detail: 'The assistant is unavailable.' } },
        { body: reply },
      ],
    })
    renderPage()
    await say('Something sweet')
    expect(await screen.findByRole('alert')).toHaveTextContent('The assistant is unavailable.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByText('Try the sorbet.')).toBeInTheDocument()
    expect(screen.getAllByText('Something sweet')).toHaveLength(1)
    const chats = fetchMock.mock.calls.filter(([url]) => String(url) === '/api/chat')
    expect(chats.map(([, init]) => init?.body)).toEqual([
      JSON.stringify({ conversation_id: 1, message: 'Something sweet' }),
      JSON.stringify({ conversation_id: 1, message: 'Something sweet' }),
    ])
  })

  test('errors that a resend cannot fix show no Retry', async () => {
    mockFetch({
      ...prefs,
      ...started,
      'POST /api/chat': { status: 404, body: { detail: 'Conversation not found.' } },
    })
    renderPage()
    await say('hi')
    expect(await screen.findByRole('alert')).toHaveTextContent('Conversation not found.')
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  test('a failed new chat can be retried', async () => {
    mockFetch({
      ...prefs,
      'POST /api/conversations': [
        { status: 503, body: { detail: 'Database is busy.' } },
        { status: 201, body: { id: 2 } },
      ],
    })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Database is busy.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await vi.waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    expect(screen.getByLabelText('Message')).toBeEnabled()
  })

  test('a lost session during a chat goes back to login', async () => {
    mockFetch({
      ...prefs,
      ...started,
      'POST /api/chat': { status: 401, body: { detail: 'Please log in.' } },
    })
    const onLogout = renderPage()
    await say('hi')
    await vi.waitFor(() => expect(onLogout).toHaveBeenCalled())
  })

  test('New chat is disabled while a reply is pending', async () => {
    mockFetch({ ...prefs, ...started })
    const pending = new Promise<Response>(() => undefined)
    const base = globalThis.fetch
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL, init?: RequestInit) =>
        String(input) === '/api/chat' ? pending : base(input, init),
      ),
    )
    renderPage()
    await say('hi')
    expect(await screen.findByRole('status')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New chat' })).toBeDisabled()
  })
})
