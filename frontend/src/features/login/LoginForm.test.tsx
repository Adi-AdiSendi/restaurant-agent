import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import { mockFetch } from '../../test/fetchMock'
import LoginForm from './LoginForm'

function fill(username: string, pin: string) {
  fireEvent.change(screen.getByLabelText('Username'), { target: { value: username } })
  fireEvent.change(screen.getByLabelText('4-digit PIN'), { target: { value: pin } })
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
}

describe('LoginForm', () => {
  test('rejects a PIN that is not 4 digits without calling the server', () => {
    const fetchMock = mockFetch({})
    render(<LoginForm onLoggedIn={vi.fn()} />)
    fill('sara', '12')
    expect(screen.getByRole('alert')).toHaveTextContent('exactly 4 digits')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  test('shows the server message for a wrong PIN', async () => {
    mockFetch({
      'POST /api/auth/login': { status: 401, body: { detail: 'Wrong PIN for this username.' } },
    })
    render(<LoginForm onLoggedIn={vi.fn()} />)
    fill('sara', '9999')
    expect(await screen.findByRole('alert')).toHaveTextContent('Wrong PIN for this username.')
  })

  test('passes the login result on success', async () => {
    mockFetch({ 'POST /api/auth/login': { body: { username: 'sara', is_new: true } } })
    const onLoggedIn = vi.fn()
    render(<LoginForm onLoggedIn={onLoggedIn} />)
    fill('Sara', '1234')
    await vi.waitFor(() =>
      expect(onLoggedIn).toHaveBeenCalledWith({ username: 'sara', is_new: true }),
    )
  })
})
