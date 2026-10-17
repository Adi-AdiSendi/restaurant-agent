import { fireEvent, render, screen } from '@testing-library/react'
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
})
