import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import type { Card } from '../../api/menuTypes'
import { kcalLabel } from '../../components/kcal'
import { latte, option } from '../../test/cards'
import ItemCard from '../chat/ItemCard'
import { initialChoice, lineKcal } from './choice'

test('kcal follow the chosen options and quantity, and say they are estimates', () => {
  const syrups = { ...latte.option_groups[1]!, options: [option(3, 'Vanilla', { kcal_delta: 40 })] }
  const item: Card = { ...latte, option_groups: [latte.option_groups[0]!, syrups] }
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
