import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import type { Card } from '../../api/menuTypes'
import { kcalLabel } from '../../components/kcal'
import { latte, option } from '../../test/cards'
import ItemCard from '../chat/ItemCard'
import { initialChoice, lineKcal } from './choice'

test('kcal follow the chosen options and quantity, and say they are estimates', () => {
  const [milk] = latte.option_groups
  const syrups = { id: 8, name: 'Syrup', min_choices: 0, max_choices: 2 }
  const vanilla = option(3, 'Vanilla', { kcal_delta: 40 })
  const groups = milk ? [milk, { ...syrups, options: [vanilla] }] : []
  const item: Card = { ...latte, option_groups: groups }
  const choice = initialChoice(item)
  expect(lineKcal(item, choice)).toBe(150)
  expect(lineKcal(item, { ...choice, optionIds: [...choice.optionIds, 3], quantity: 2 })).toBe(380)
  expect(lineKcal({ ...item, kcal: null }, choice)).toBeNull()
  expect(kcalLabel(1800)).toBe('about 1,800 kcal (estimate)')
  expect(kcalLabel(null)).toBeNull()
})

test('a card shows its estimate', () => {
  render(<ItemCard item={latte} />)
  expect(screen.getByText('about 150 kcal (estimate)')).toBeInTheDocument()
})

test('a dish sold in packs says so', () => {
  render(<ItemCard item={{ ...latte, name: 'Khalas Dates', pack_size: 3, pack_unit: 'dates' }} />)
  expect(screen.getByText('Sold in packs of 3 dates.')).toBeInTheDocument()
})
