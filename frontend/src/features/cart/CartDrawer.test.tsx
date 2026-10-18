import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { describe, expect, test, vi } from 'vitest'

import { emptyCart, latteCart, oatLatte } from '../../test/carts'
import { mockFetch } from '../../test/fetchMock'
import CartButton from './CartButton'
import CartProvider from './CartProvider'

function renderCart() {
  render(
    <MemoryRouter>
      <CartProvider onUnauthorized={vi.fn()}>
        <CartButton />
      </CartProvider>
    </MemoryRouter>,
  )
}

describe('cart drawer', () => {
  test('the button shows the count and opens the lines with their total', async () => {
    mockFetch({ 'GET /api/cart': { body: latteCart } })
    renderCart()
    fireEvent.click(await screen.findByRole('button', { name: 'Cart2' }))
    const drawer = screen.getByRole('dialog', { name: 'Your cart' })
    expect(drawer).toHaveTextContent('Bean & Bloom')
    expect(drawer).toHaveTextContent('Oat milk, no sugar')
    expect(drawer).toHaveTextContent('38.00 SAR')
    expect(screen.getByRole('link', { name: 'Checkout' })).toHaveAttribute('href', '/checkout')
  })

  test('Escape closes the drawer', async () => {
    mockFetch({ 'GET /api/cart': { body: latteCart } })
    renderCart()
    fireEvent.click(await screen.findByRole('button', { name: 'Cart2' }))
    expect(screen.getByRole('dialog', { name: 'Your cart' })).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('plus and remove ask the server and show the cart it returns', async () => {
    const three = { ...oatLatte, quantity: 3, line_total_sar: '57.00' }
    const fetchMock = mockFetch({
      'GET /api/cart': { body: latteCart },
      'PATCH /api/cart/lines/9': { body: { ...latteCart, lines: [three], item_count: 3 } },
      'DELETE /api/cart/lines/9': { body: emptyCart },
    })
    renderCart()
    fireEvent.click(await screen.findByRole('button', { name: 'Cart2' }))
    fireEvent.click(screen.getByRole('button', { name: 'One more Latte' }))
    expect(await screen.findByText('57.00 SAR')).toBeInTheDocument()
    const patch = fetchMock.mock.calls.find(([url]) => String(url) === '/api/cart/lines/9')
    expect(patch?.[1]?.body).toBe(JSON.stringify({ quantity: 3 }))
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    expect(await screen.findByText(/Your cart is empty/)).toBeInTheDocument()
  })

  test('an unavailable line blocks checkout and says why', async () => {
    const gone = { ...oatLatte, problem: 'The menu changed.', line_total_sar: null }
    mockFetch({ 'GET /api/cart': { body: { ...latteCart, lines: [gone] } } })
    renderCart()
    fireEvent.click(await screen.findByRole('button', { name: 'Cart2' }))
    expect(screen.getByText('The menu changed.')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Checkout' })).not.toBeInTheDocument()
  })
})
