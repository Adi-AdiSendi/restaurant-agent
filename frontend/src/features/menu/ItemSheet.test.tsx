import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { Card } from '../../api/menuTypes'
import { emptyCart } from '../../test/carts'
import { latte, option } from '../../test/cards'
import { mockFetch } from '../../test/fetchMock'
import CartProvider from '../cart/CartProvider'
import ItemSheet from './ItemSheet'

const added = { body: { ...emptyCart, item_count: 1 } }
const conflict = {
  status: 409,
  body: {
    detail: {
      code: 'conflict',
      message: 'Latte as chosen is not suitable: dairy.',
      reasons: ['dairy'],
    },
  },
}
const other = {
  status: 409,
  body: {
    detail: { code: 'other_restaurant', message: 'Cart elsewhere.', restaurant: 'Stack & Smash' },
  },
}

/** A latte with an optional single choice: at most one, and none is fine. */
const latteWithShot: Card = {
  ...latte,
  option_groups: [
    ...latte.option_groups,
    { id: 9, name: 'Shot', min_choices: 0, max_choices: 1, options: [option(6, 'Extra shot')] },
  ],
}

function renderSheet(onClose = vi.fn(), item = latte) {
  render(
    <CartProvider onUnauthorized={vi.fn()}>
      <ItemSheet
        item={item}
        restaurant="bean-and-bloom"
        onClose={onClose}
        onUnauthorized={vi.fn()}
      />
    </CartProvider>,
  )
  return onClose
}

const sentBodies = (fetchMock: ReturnType<typeof mockFetch>) =>
  fetchMock.mock.calls
    .filter(([url]) => String(url) === '/api/cart/lines')
    .map(([, init]) => JSON.parse(String(init?.body)) as Record<string, unknown>)

describe('ItemSheet', () => {
  test('it starts on a milk that suits the guest and adds with the live price', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': added,
    })
    const onClose = renderSheet()
    expect(screen.getByRole('radio', { name: /Oat milk/ })).toBeChecked()
    fireEvent.click(screen.getByRole('checkbox', { name: /Vanilla/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Add to cart · 21.00 SAR' }))
    await vi.waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(sentBodies(fetchMock)[0]).toMatchObject({
      item_id: 40,
      option_ids: [2, 3],
      accepted_reasons: [],
    })
  })

  test('a conflicting choice is warned about, and only added after "Add anyway"', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': [conflict, added],
    })
    const onClose = renderSheet()
    fireEvent.click(screen.getByRole('radio', { name: /Whole milk/ }))
    expect(screen.getByRole('note')).toHaveTextContent('not suitable for you: dairy')
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('Add it anyway?')
    expect(onClose).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Add anyway' }))
    await vi.waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(sentBodies(fetchMock).map((b) => b.accepted_reasons)).toEqual([[], ['dairy']])
  })

  test('a cart at another restaurant is only replaced when the guest agrees', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': [other, other, added],
    })
    renderSheet()
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    expect(await screen.findByRole('alertdialog')).toHaveTextContent('dishes from Stack & Smash')
    fireEvent.click(screen.getByRole('button', { name: 'Keep my cart' }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Start a new cart' }))
    await vi.waitFor(() => expect(sentBodies(fetchMock)).toHaveLength(3))
    expect(sentBodies(fetchMock).map((b) => b.replace_cart)).toEqual([false, false, true])
  })

  test('consent covers only the choice it was given for; a change asks again', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': conflict,
    })
    renderSheet()
    fireEvent.click(screen.getByRole('radio', { name: /Whole milk/ }))
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Add anyway' }))
    fireEvent.click(await screen.findByRole('button', { name: 'No, keep it out' }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Vanilla/ }))
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    await vi.waitFor(() => expect(sentBodies(fetchMock)).toHaveLength(3))
    expect(sentBodies(fetchMock).map((b) => b.accepted_reasons)).toEqual([[], ['dairy'], []])
  })

  test('an optional single choice is a checkbox that can be cleared', async () => {
    const fetchMock = mockFetch({
      'GET /api/cart': { body: emptyCart },
      'POST /api/cart/lines': added,
    })
    const onClose = renderSheet(vi.fn(), latteWithShot)
    const shot = screen.getByRole('checkbox', { name: /Extra shot/ })
    fireEvent.click(shot)
    expect(shot).toBeChecked()
    fireEvent.click(shot)
    expect(shot).not.toBeChecked()
    fireEvent.click(screen.getByRole('button', { name: /Add to cart/ }))
    await vi.waitFor(() => expect(onClose).toHaveBeenCalled())
    expect(sentBodies(fetchMock)[0]).toMatchObject({ option_ids: [2] })
  })

  test('Escape closes the sheet', () => {
    mockFetch({ 'GET /api/cart': { body: emptyCart } })
    const onClose = renderSheet()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalled()
  })
})
