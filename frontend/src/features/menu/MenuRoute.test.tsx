import { act, fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, test, vi } from 'vitest'

import { cartRoute } from '../../test/carts'
import { mockFetch } from '../../test/fetchMock'
import { dragonMenu, restaurants } from '../../test/restaurants'
import CartProvider from '../cart/CartProvider'
import MenuRoute from './MenuRoute'

const corner = restaurants['GET /api/restaurants'].body[0]

test('another restaurant starts afresh: an open sheet does not carry over', async () => {
  mockFetch({
    ...dragonMenu,
    ...cartRoute,
    'GET /api/restaurants/corner-table/menu': { body: { restaurant: corner, items: [] } },
    'POST /api/conversations': { status: 201, body: { id: 5 } },
    'GET /api/preferences': { body: [] },
  })
  const page = <MenuRoute username="sara" isNew={false} onLogout={vi.fn()} />
  const router = createMemoryRouter([{ path: '/r/:slug', element: page }], {
    initialEntries: ['/r/golden-dragon'],
  })
  render(
    <CartProvider onUnauthorized={vi.fn()}>
      <RouterProvider router={router} />
    </CartProvider>,
  )
  fireEvent.click(await screen.findByRole('button', { name: 'Choose options' }))
  expect(screen.getByRole('dialog', { name: 'Latte' })).toBeInTheDocument()
  await act(() => router.navigate('/r/corner-table'))
  expect(await screen.findByRole('heading', { name: 'Corner Table' })).toBeInTheDocument()
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
})
