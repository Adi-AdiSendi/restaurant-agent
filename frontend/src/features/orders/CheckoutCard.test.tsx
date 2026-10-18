import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, test, vi } from 'vitest'

import { emptyCart, latteCart, oatLatte, placedOrder } from '../../test/carts'
import { mockFetch } from '../../test/fetchMock'
import CartProvider from '../cart/CartProvider'
import CheckoutCard from './CheckoutCard'

function renderCard() {
  render(
    <MemoryRouter>
      <CartProvider onUnauthorized={vi.fn()}>
        <Routes>
          <Route path="/" element={<CheckoutCard />} />
          <Route path="/orders/:id" element={<p>Order page</p>} />
        </Routes>
      </CartProvider>
    </MemoryRouter>,
  )
}

const conflict = {
  status: 409,
  body: { detail: { code: 'conflict', message: 'Not suitable: dairy.', reasons: ['dairy'] } },
}

const placedBodies = (fetchMock: ReturnType<typeof mockFetch>) =>
  fetchMock.mock.calls
    .filter(([url, init]) => String(url) === '/api/orders' && init?.method === 'POST')
    .map(([, init]) => JSON.parse(String(init?.body)) as Record<string, unknown>)

describe('chat checkout card', () => {
  test("the guest's button places the order and opens it", async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': [{ body: latteCart }, { body: emptyCart }],
      'POST /api/orders': { status: 201, body: placedOrder },
    })
    renderCard()
    expect(await screen.findByText(/2 items · 38.00 SAR/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('radio', { name: 'Dine in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Place order · 38.00 SAR' }))
    expect(await screen.findByText('Order page')).toBeInTheDocument()
    expect(placedBodies(fetchMock)).toEqual([
      { fulfilment: 'dine_in', accepted_reasons: [], expected_total_sar: '38.00' },
    ])
  })

  test('a conflict asks the guest, and only their answer resends', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: latteCart },
      'POST /api/orders': [conflict, { status: 201, body: placedOrder }],
    })
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Place order/ }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('Not suitable: dairy.')
    fireEvent.click(screen.getByRole('button', { name: 'Place it anyway' }))
    expect(await screen.findByText('Order page')).toBeInTheDocument()
    expect(placedBodies(fetchMock).map((b) => b.accepted_reasons)).toEqual([[], ['dairy']])
  })

  test('a cart that changed since the guest looked is shown again, not ordered', async () => {
    const changed = {
      status: 409,
      body: { detail: { code: 'cart_changed', message: 'Your cart changed since you looked.' } },
    }
    mockFetch({ 'GET /api/cart': { body: latteCart }, 'POST /api/orders': changed })
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Place order/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Your cart changed')
    expect(screen.queryByText('Order page')).not.toBeInTheDocument()
  })

  test('unavailable dishes block the order', async () => {
    const gone = { ...oatLatte, problem: 'The menu changed.', line_total_sar: null }
    mockFetch({ 'GET /api/cart': { body: { ...latteCart, lines: [gone] } } })
    renderCard()
    expect(await screen.findByText(/Remove the unavailable dishes/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Place order/ })).not.toBeInTheDocument()
  })

  test('an empty cart offers no button', async () => {
    mockFetch({ 'GET /api/cart': { body: emptyCart } })
    renderCard()
    expect(await screen.findByText('Your cart is empty.')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
