import { act, fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router'
import { expect, test, vi } from 'vitest'

import { cartRoute } from '../../test/carts'
import { latteAdded } from '../../test/chat'
import { mockFetch } from '../../test/fetchMock'
import { dragonMenu, restaurants } from '../../test/restaurants'
import CartButton from '../cart/CartButton'
import CartProvider from '../cart/CartProvider'
import MenuRoute from './MenuRoute'

const corner = restaurants['GET /api/restaurants'].body[0]
const chatRoutes = {
  'POST /api/conversations': { status: 201, body: { id: 5 } },
  'GET /api/preferences': { body: [] },
}

test('another restaurant starts afresh: an open sheet does not carry over', async () => {
  mockFetch({
    ...dragonMenu,
    ...cartRoute,
    'GET /api/restaurants/corner-table/menu': { body: { restaurant: corner, items: [] } },
    ...chatRoutes,
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

test('a chat reply updates the cart from the cart it carries, with no reload', async () => {
  // The server's GET /api/cart stays empty: only the reply can fill the cart button.
  mockFetch({ ...dragonMenu, ...cartRoute, ...chatRoutes, 'POST /api/chat': { body: latteAdded } })
  const page = <MenuRoute username="sara" isNew={false} onLogout={vi.fn()} />
  const routes = [{ path: '/r/:slug', element: [<CartButton key="cart" />, page] }]
  const router = createMemoryRouter(routes, { initialEntries: ['/r/golden-dragon'] })
  render(
    <CartProvider onUnauthorized={vi.fn()}>
      <RouterProvider router={router} />
    </CartProvider>,
  )
  fireEvent.change(await screen.findByRole('textbox', { name: 'Message' }), {
    target: { value: 'Two oat lattes' },
  })
  const send = screen.getByRole('button', { name: 'Send' })
  await vi.waitFor(() => expect(send).toBeEnabled())
  fireEvent.click(send)
  expect(await screen.findByText('Added 2 × Latte')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Cart2' })).toBeInTheDocument()
})
