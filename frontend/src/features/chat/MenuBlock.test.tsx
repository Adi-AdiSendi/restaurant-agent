import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import type { Card } from '../../api/menuTypes'
import { latte } from '../../test/cards'
import MenuBlock from './MenuBlock'

const water: Card = { ...latte, id: 41, name: 'Still Water', option_groups: [], price_sar: '6.00' }
const milkshake: Card = { ...water, id: 42, name: 'Milkshake', conflicts_with_guest: ['dairy'] }
const block = { category: 'coffee', items: [latte, water, milkshake] }

test('every dish shows; unsuitable ones say why and cannot be added', () => {
  const quickAdd = { add: vi.fn(), added: null }
  const onChoose = vi.fn()
  render(<MenuBlock block={block} onChoose={onChoose} quickAdd={quickAdd} />)
  expect(screen.getByRole('region', { name: 'Menu: Coffee' })).toBeInTheDocument()
  expect(screen.getByText('not for you: dairy')).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /Milkshake/ })).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Add Still Water to the cart' }))
  expect(quickAdd.add).toHaveBeenCalledWith(water)
  fireEvent.click(screen.getByRole('button', { name: 'Options' }))
  expect(onChoose).toHaveBeenCalledWith(latte)
  expect(screen.getByText('from 16.00 SAR')).toBeInTheDocument()
})

test('a dish just added says so', () => {
  render(<MenuBlock block={block} quickAdd={{ add: vi.fn(), added: 41 }} />)
  expect(screen.getByRole('button', { name: 'Add Still Water to the cart' })).toHaveTextContent(
    'Added ✓',
  )
})
