import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { mockFetch } from '../../test/fetchMock'
import { restaurants } from '../../test/restaurants'
import ChatPage from './ChatPage'

const prefs = { 'GET /api/preferences': { body: [] } }
const started = { 'POST /api/conversations': { status: 201, body: { id: 1 } } }

function renderPage() {
  render(<ChatPage username="sara" isNew={false} onLogout={vi.fn()} />)
}

describe('ChatPage restaurants', () => {
  test('a chat starts at the remembered restaurant, and the picker starts a new one', async () => {
    localStorage.setItem('restaurant', 'golden-dragon')
    const fetchMock = mockFetch({ ...prefs, ...restaurants, ...started })
    renderPage()
    const picker = await screen.findByRole('combobox', { name: 'Restaurant' })
    await vi.waitFor(() => expect(picker).toHaveValue('golden-dragon'))
    fireEvent.change(picker, { target: { value: 'corner-table' } })
    await vi.waitFor(() => {
      const starts = fetchMock.mock.calls.filter(([url]) => String(url) === '/api/conversations')
      expect(starts.map(([, init]) => init?.body)).toEqual([
        JSON.stringify({ restaurant: 'golden-dragon' }),
        JSON.stringify({ restaurant: 'corner-table' }),
      ])
    })
    expect(localStorage.getItem('restaurant')).toBe('corner-table')
    localStorage.clear()
  })

  test('a failed restaurant list shows Retry, which loads it again', async () => {
    mockFetch({
      ...prefs,
      ...started,
      'GET /api/restaurants': [
        { status: 503, body: { detail: 'Busy.' } },
        restaurants['GET /api/restaurants'],
      ],
    })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Busy.')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(await screen.findByRole('combobox', { name: 'Restaurant' })).toHaveValue('corner-table')
  })

  test('a slow start for an earlier pick never replaces a later one', async () => {
    mockFetch({ ...prefs, ...restaurants })
    const base = globalThis.fetch
    const pending: ((id: number) => void)[] = []
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        if (String(input) !== '/api/conversations') return base(input, init)
        return new Promise<Response>((resolve) => {
          pending.push((id) => resolve(new Response(JSON.stringify({ id }), { status: 201 })))
        })
      }),
    )
    renderPage()
    const picker = await screen.findByRole('combobox', { name: 'Restaurant' })
    await vi.waitFor(() => expect(pending).toHaveLength(1))
    fireEvent.change(picker, { target: { value: 'golden-dragon' } })
    await vi.waitFor(() => expect(pending).toHaveLength(2))
    await act(async () => pending[1]?.(22))
    await act(async () => pending[0]?.(11))
    const input = screen.getByLabelText('Message')
    fireEvent.change(input, { target: { value: 'hi' } })
    await vi.waitFor(() => expect(screen.getByRole('button', { name: 'Send' })).toBeEnabled())
    const sent = vi.fn(() => Promise.resolve(new Response('{}', { status: 500 })))
    vi.stubGlobal('fetch', sent)
    fireEvent.click(screen.getByRole('button', { name: 'Send' }))
    await vi.waitFor(() => expect(sent).toHaveBeenCalled())
    expect(sent.mock.calls[0]).toEqual([
      '/api/chat',
      expect.objectContaining({ body: JSON.stringify({ conversation_id: 22, message: 'hi' }) }),
    ])
  })

  test('an empty restaurant list says so', async () => {
    mockFetch({ ...prefs, ...started, 'GET /api/restaurants': { body: [] } })
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('No restaurants are set up yet.')
  })
})
