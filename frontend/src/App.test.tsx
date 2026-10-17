import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'

import App from './App'
import { GIVE_UP_MS, RETRY_MS, SLOW_MS } from './features/startup/useServerReady'
import { mockFetch } from './test/fetchMock'
import { restaurants } from './test/restaurants'

const UP = { body: { status: 'ok' } }
const LOGGED_OUT = { status: 401, body: { detail: 'Please log in.' } }

afterEach(() => {
  vi.useRealTimers()
})

test('shows the login form when there is no session', async () => {
  mockFetch({ 'GET /api/health': UP, 'GET /api/auth/me': LOGGED_OUT })
  render(<App />)
  expect(
    await screen.findByRole('heading', { name: 'Foodics Order Assistant' }),
  ).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument()
})

const SIGNED_IN = {
  'GET /api/health': UP,
  'GET /api/auth/me': { body: { username: 'sara' } },
  'POST /api/conversations': { status: 201, body: { id: 5 } },
  ...restaurants,
  'GET /api/preferences': { body: [] },
}

test('a returning session opens the restaurants page with the app header', async () => {
  window.history.pushState({}, '', '/')
  mockFetch(SIGNED_IN)
  render(<App />)
  expect(await screen.findByRole('link', { name: /Golden Dragon/ })).toBeInTheDocument()
  expect(screen.getByRole('navigation', { name: 'Main' })).toBeInTheDocument()
  expect(screen.getByText('Hi, sara')).toBeInTheDocument()
})

test('a restaurant link opens its chat and the memory panel', async () => {
  window.history.pushState({}, '', '/r/golden-dragon')
  mockFetch(SIGNED_IN)
  render(<App />)
  expect(await screen.findByText(/Welcome back, sara!/)).toBeInTheDocument()
  expect(
    screen.getByRole('complementary', { name: 'What I remember about you' }),
  ).toBeInTheDocument()
  window.history.pushState({}, '', '/')
})

test('an unknown path goes back to the restaurants', async () => {
  window.history.pushState({}, '', '/nowhere')
  mockFetch(SIGNED_IN)
  render(<App />)
  expect(await screen.findByRole('link', { name: /Corner Table/ })).toBeInTheDocument()
  expect(window.location.pathname).toBe('/')
})

test('a sleeping server shows the startup screen, then the app once it answers', async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  mockFetch({
    'GET /api/health': [{ status: 504, body: null }, UP],
    'GET /api/auth/me': LOGGED_OUT,
  })
  render(<App />)
  expect(await screen.findByText('Starting the server…')).toBeInTheDocument()
  await act(() => vi.advanceTimersByTimeAsync(RETRY_MS))
  expect(await screen.findByRole('button', { name: 'Continue' })).toBeInTheDocument()
})

test('after two minutes it gives up and offers a retry', async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  const fetchMock = mockFetch({ 'GET /api/health': { status: 504 } })
  render(<App />)
  await act(() => vi.advanceTimersByTimeAsync(GIVE_UP_MS + RETRY_MS))
  expect(await screen.findByRole('alert')).toHaveTextContent('The server did not start.')

  mockFetch({ 'GET /api/health': UP, 'GET /api/auth/me': LOGGED_OUT })
  fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
  expect(await screen.findByRole('button', { name: 'Continue' })).toBeInTheDocument()
  expect(fetchMock.mock.calls.length).toBeGreaterThan(10)
})

test('a health check that hangs shows the startup screen after a second', async () => {
  vi.useFakeTimers({ shouldAdvanceTime: true })
  vi.stubGlobal(
    'fetch',
    vi.fn(() => new Promise<Response>(() => undefined)),
  )
  render(<App />)
  expect(screen.queryByText('Starting the server…')).not.toBeInTheDocument()
  await act(() => vi.advanceTimersByTimeAsync(SLOW_MS))
  expect(screen.getByText('Starting the server…')).toBeInTheDocument()
})
