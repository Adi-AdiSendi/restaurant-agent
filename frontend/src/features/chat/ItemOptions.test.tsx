import { render, screen, within } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import type { Card, CardOption } from '../../api/menuTypes'
import ItemCard from './ItemCard'

function option(id: number, name: string, extra: Partial<CardOption> = {}): CardOption {
  return {
    id,
    name,
    price_delta_sar: '0.00',
    allergens: [],
    may_contain: [],
    is_vegetarian: true,
    is_vegan: true,
    spice_level: 0,
    conflicts_with_guest: [],
    may_contain_warnings: [],
    ...extra,
  }
}

const latte: Card = {
  id: 40,
  name: 'Latte',
  category: 'coffee',
  description: 'Espresso with steamed milk.',
  price_sar: '16.00',
  is_vegetarian: true,
  is_vegan: true,
  spice_level: 0,
  ingredients: ['espresso', 'sugar'],
  allergens: [],
  may_contain: [],
  removable: ['sugar'],
  option_groups: [
    {
      id: 7,
      name: 'Milk',
      min_choices: 1,
      max_choices: 1,
      options: [
        option(1, 'Whole milk', { allergens: ['dairy'], conflicts_with_guest: ['dairy'] }),
        option(2, 'Oat milk', { price_delta_sar: '3.00', may_contain_warnings: ['gluten'] }),
      ],
    },
    {
      id: 8,
      name: 'Syrup',
      min_choices: 0,
      max_choices: 2,
      options: [option(3, 'Vanilla'), option(4, 'Chilli', { spice_level: 3 })],
    },
  ],
  conflicts_with_guest: [],
  may_contain_warnings: [],
}

describe('ItemCard options', () => {
  test('a dish with options shows a starting price and every group with its rule', () => {
    render(<ItemCard item={latte} />)
    expect(screen.getByText('from 16.00 SAR')).toBeInTheDocument()
    expect(screen.getByText('(choose 1)')).toBeInTheDocument()
    expect(screen.getByText('(optional, up to 2)')).toBeInTheDocument()
    expect(screen.getByText('Oat milk +3.00')).toBeInTheDocument()
    expect(screen.getByText('Can be made without: sugar.')).toBeInTheDocument()
  })

  test('an option that breaks the guest profile says why, with its allergens', () => {
    render(<ItemCard item={latte} />)
    const whole = screen.getByText('Whole milk').closest('li')
    expect(whole).not.toBeNull()
    expect(within(whole as HTMLElement).getByText(/contains dairy/)).toBeInTheDocument()
    expect(within(whole as HTMLElement).getByText(/not for you: dairy/)).toBeInTheDocument()
  })

  test('a dish without options shows a plain price', () => {
    render(<ItemCard item={{ ...latte, option_groups: [], removable: [] }} />)
    expect(screen.getByText('16.00 SAR')).toBeInTheDocument()
    expect(screen.queryByText(/Can be made without/)).not.toBeInTheDocument()
  })

  test('an option shows its spice and any trace the guest avoids', () => {
    render(<ItemCard item={latte} />)
    const oat = screen.getByText('Oat milk +3.00').closest('li') as HTMLElement
    expect(within(oat).getByText(/may contain gluten/)).toBeInTheDocument()
    const chilli = screen.getByText('Chilli').closest('li') as HTMLElement
    expect(within(chilli).getByText(/hot/)).toBeInTheDocument()
  })
})
