import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { expect, test } from 'vitest'

import { placedOrder } from '../../test/carts'
import OrderCard from './OrderCard'
import OrderDetail from './OrderDetail'

test('a past order shows the sign, dish photos, status and the price paid', () => {
  const { container } = render(
    <MemoryRouter>
      <OrderCard order={{ ...placedOrder, item_count: 3 }} />
    </MemoryRouter>,
  )
  const srcs = [...container.querySelectorAll('img')].map((img) => img.getAttribute('src'))
  expect(srcs).toEqual([
    '/storefronts/bean-and-bloom-1440.webp',
    '/menu/bean-and-bloom/latte-320.webp',
  ])
  expect(screen.getByText('+2')).toBeInTheDocument()
  expect(screen.getByText('38.00 SAR')).toBeInTheDocument()
  expect(screen.getByText('Preparing')).toBeInTheDocument()
})

test('the receipt shows each dish with its photo, line total and the total paid', () => {
  render(
    <MemoryRouter>
      <OrderDetail order={placedOrder} />
    </MemoryRouter>,
  )
  expect(screen.getByText('2 × Latte')).toBeInTheDocument()
  expect(screen.getByText('19.00 SAR each')).toBeInTheDocument()
  expect(screen.getAllByText('38.00 SAR')).toHaveLength(2)
  expect(screen.getByText('Total paid at the counter')).toBeInTheDocument()
  expect(screen.getByRole('listitem', { current: 'step' })).toHaveTextContent('Preparing')
})
