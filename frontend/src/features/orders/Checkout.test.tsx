import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { describe, expect, test, vi } from 'vitest'

import { emptyCart, latteCart, placedOrder } from '../../test/carts'
import { mockFetch } from '../../test/fetchMock'
import CartProvider from '../cart/CartProvider'
import CheckoutPage from './CheckoutPage'
import OrderPage from './OrderPage'
import OrdersPage from './OrdersPage'

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <CartProvider onUnauthorized={vi.fn()}>
        <Routes>
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/:id" element={<OrderPage />} />
        </Routes>
      </CartProvider>
    </MemoryRouter>,
  )
}

const conflict = {
  status: 409,
  body: { detail: { code: 'conflict', message: 'Not suitable: dairy.', reasons: ['dairy'] } },
}

describe('checkout and orders', () => {
  test('placing an order goes to its page', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': [{ body: latteCart }, { body: emptyCart }],
      'POST /api/orders': { status: 201, body: placedOrder },
      'GET /api/orders/31': { body: placedOrder },
    })
    renderAt('/checkout')
    fireEvent.click(await screen.findByRole('radio', { name: 'Dine in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Place order · 38.00 SAR' }))
    expect(
      await screen.findByRole('heading', { name: 'Order 31 · Bean & Bloom' }),
    ).toBeInTheDocument()
    expect(screen.getByText('Preparing')).toBeInTheDocument()
    const placed = fetchMock.mock.calls.find(([url]) => String(url) === '/api/orders')
    expect(placed?.[1]?.body).toBe(
      JSON.stringify({ fulfilment: 'dine_in', accept_conflicts: false }),
    )
  })

  test('a conflict at checkout needs "Place it anyway"', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: latteCart },
      'POST /api/orders': [conflict, { status: 201, body: placedOrder }],
      'GET /api/orders/31': { body: placedOrder },
    })
    renderAt('/checkout')
    fireEvent.click(await screen.findByRole('button', { name: /Place order/ }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('Not suitable: dairy.')
    fireEvent.click(screen.getByRole('button', { name: 'Place it anyway' }))
    expect(await screen.findByRole('heading', { name: /Order 31/ })).toBeInTheDocument()
    const bodies = fetchMock.mock.calls
      .filter(([url]) => String(url) === '/api/orders')
      .map(([, init]) => JSON.parse(String(init?.body)) as { accept_conflicts: boolean })
    expect(bodies.map((b) => b.accept_conflicts)).toEqual([false, true])
  })

  test('an empty cart cannot be checked out', async () => {
    mockFetch({ 'GET /api/cart': { body: emptyCart } })
    renderAt('/checkout')
    expect(await screen.findByText(/Your cart is empty/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Place order/ })).not.toBeInTheDocument()
  })

  test('the orders list links each order', async () => {
    mockFetch({
      'GET /api/cart': { body: emptyCart },
      'GET /api/orders': { body: [placedOrder] },
      'GET /api/orders/99': {
        status: 404,
        body: { detail: { code: 'not_found', message: 'No such order.' } },
      },
    })
    renderAt('/orders')
    expect(await screen.findByRole('link', { name: 'Order 31 · Bean & Bloom' })).toHaveAttribute(
      'href',
      '/orders/31',
    )
  })

  test("another guest's order, or a missing one, is not found", async () => {
    mockFetch({
      'GET /api/cart': { body: emptyCart },
      'GET /api/orders/99': {
        status: 404,
        body: { detail: { code: 'not_found', message: 'No such order.' } },
      },
    })
    renderAt('/orders/99')
    expect(await screen.findByRole('alert')).toHaveTextContent('No such order.')
  })
})
