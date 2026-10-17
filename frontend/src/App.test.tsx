import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import App from './App'
import { mockFetch } from './test/fetchMock'

test('shows the login form when there is no session', async () => {
  mockFetch({ 'GET /api/auth/me': { status: 401, body: { detail: 'Please log in.' } } })
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Corner Table' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Continue' })).toBeInTheDocument()
})

test('a returning session opens the chat with a greeting and the memory panel', async () => {
  mockFetch({
    'GET /api/auth/me': { body: { username: 'sara' } },
    'POST /api/conversations': { status: 201, body: { id: 5 } },
    'GET /api/preferences': { body: [] },
  })
  render(<App />)
  expect(await screen.findByText(/Welcome back, sara!/)).toBeInTheDocument()
  expect(
    screen.getByRole('complementary', { name: 'What I remember about you' }),
  ).toBeInTheDocument()
  expect(
    await screen.findByRole('button', { name: 'Something vegan under 45 SAR' }),
  ).toBeInTheDocument()
})
