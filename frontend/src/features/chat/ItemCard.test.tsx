import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'

import type { Card } from '../../api/menuTypes'
import ItemCard from './ItemCard'

const cake: Card = {
  id: 15,
  name: 'Chocolate Lava Cake',
  category: 'desserts_and_drinks',
  description: 'Warm chocolate cake.',
  price_sar: '34.00',
  is_vegetarian: true,
  is_vegan: false,
  spice_level: 0,
  ingredients: ['dark chocolate', 'egg'],
  allergens: ['gluten', 'dairy', 'egg'],
  may_contain: ['tree_nut'],
  removable: [],
  photo: null,
  option_groups: [],
  conflicts_with_guest: [],
  may_contain_warnings: [],
}

describe('ItemCard', () => {
  test('shows name, price, diet and every allergen from the card data', () => {
    render(<ItemCard item={cake} />)
    expect(screen.getByRole('heading', { name: 'Chocolate Lava Cake' })).toBeInTheDocument()
    expect(screen.getByText('34.00 SAR')).toBeInTheDocument()
    expect(screen.getByText('Vegetarian')).toBeInTheDocument()
    for (const allergen of ['gluten', 'dairy', 'egg']) {
      expect(screen.getByText(allergen)).toBeInTheDocument()
    }
  })

  test('shows traces as information when the guest does not avoid them', () => {
    render(<ItemCard item={cake} />)
    expect(screen.getByText('May contain traces of tree nut.')).toBeInTheDocument()
    expect(screen.queryByRole('note')).not.toBeInTheDocument()
  })

  test('shows a warning when a trace allergen is one the guest avoids', () => {
    render(<ItemCard item={{ ...cake, may_contain_warnings: ['tree_nut'] }} />)
    expect(screen.getByRole('note')).toHaveTextContent('May contain tree nut, which you avoid')
    expect(screen.queryByText('May contain traces of tree nut.')).not.toBeInTheDocument()
  })

  test('says so when no allergens are listed, and marks vegan items', () => {
    render(<ItemCard item={{ ...cake, allergens: [], may_contain: [], is_vegan: true }} />)
    expect(screen.getByText('none listed')).toBeInTheDocument()
    expect(screen.getByText('Vegan')).toBeInTheDocument()
  })
})
