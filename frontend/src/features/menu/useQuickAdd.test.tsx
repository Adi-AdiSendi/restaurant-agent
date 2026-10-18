import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { Card } from '../../api/menuTypes'
import { emptyCart, latteCart } from '../../test/carts'
import { latte } from '../../test/cards'
import { mockFetch } from '../../test/fetchMock'
import CartButton from '../cart/CartButton'
import CartProvider from '../cart/CartProvider'
import ItemCard from '../chat/ItemCard'
import { useQuickAdd } from './useQuickAdd'

const cake: Card = { ...latte, id: 50, name: 'Lemon Cake', option_groups: [], removable: [] }

function Shelf({ item, onNeedsSheet }: { item: Card; onNeedsSheet: (item: Card) => void }) {
  const quickAdd = useQuickAdd({
    restaurant: 'bean-and-bloom',
    onNeedsSheet,
    onUnauthorized: vi.fn(),
  })
  return <ItemCard item={item} onChoose={() => onNeedsSheet(item)} quickAdd={quickAdd} />
}

function renderShelf(item: Card, onNeedsSheet = vi.fn()) {
  render(
    <CartProvider onUnauthorized={vi.fn()}>
      <CartButton />
      <Shelf item={item} onNeedsSheet={onNeedsSheet} />
    </CartProvider>,
  )
  return onNeedsSheet
}

describe('quick add', () => {
  test('a dish with no choices is added in one click and the cart updates', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': { body: latteCart },
    })
    renderShelf(cake)
    fireEvent.click(screen.getByRole('button', { name: 'Add Lemon Cake to the cart' }))
    expect(await screen.findByText('Added ✓')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cart2' })).toBeInTheDocument()
    const sent = fetchMock.mock.calls.find(([url]) => String(url) === '/api/cart/lines')
    expect(JSON.parse(String(sent?.[1]?.body))).toMatchObject({ item_id: 50, option_ids: [] })
  })

  test('a double click adds once', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': { body: latteCart },
    })
    renderShelf(cake)
    const add = screen.getByRole('button', { name: 'Add Lemon Cake to the cart' })
    fireEvent.click(add)
    fireEvent.click(add)
    expect(await screen.findByText('Added ✓')).toBeInTheDocument()
    const posts = fetchMock.mock.calls.filter(([url]) => String(url) === '/api/cart/lines')
    expect(posts).toHaveLength(1)
  })

  test('a dish with a removable ingredient goes through the sheet', () => {
    mockFetch({ 'GET /api/cart': { body: emptyCart } })
    renderShelf({ ...cake, removable: ['icing'] })
    expect(screen.queryByRole('button', { name: /to the cart/ })).not.toBeInTheDocument()
  })

  test('anything the server asks about opens the sheet instead', async () => {
    const conflict = { status: 409, body: { detail: { code: 'other_restaurant', message: 'x' } } }
    mockFetch({ 'GET /api/cart': { body: emptyCart }, 'POST /api/cart/lines': conflict })
    const onNeedsSheet = renderShelf(cake)
    fireEvent.click(screen.getByRole('button', { name: 'Add Lemon Cake to the cart' }))
    await vi.waitFor(() => expect(onNeedsSheet).toHaveBeenCalledWith(cake))
  })

  test('a dish with a required choice, or a conflict, still opens the sheet', () => {
    mockFetch({ 'GET /api/cart': { body: emptyCart } })
    renderShelf(latte)
    expect(screen.queryByRole('button', { name: /to the cart/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Choose options' })).toBeInTheDocument()
  })
})
