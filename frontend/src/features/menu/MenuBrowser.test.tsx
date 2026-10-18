import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { GuestMenu } from '../../api/menuTypes'
import { latte } from '../../test/cards'
import MenuBrowser from './MenuBrowser'

const menu: GuestMenu = {
  restaurant: {
    id: 3,
    slug: 'bean-and-bloom',
    name: 'Bean & Bloom',
    cuisine: 'Cafe',
    tagline: 'T.',
    accent_color: '#2b8a3e',
    categories: ['coffee', 'bakery_and_cakes'],
    photo: null,
  },
  items: [
    latte,
    {
      ...latte,
      id: 41,
      name: 'Butter Croissant',
      description: 'Flaky and golden.',
      category: 'bakery_and_cakes',
      ingredients: ['wheat flour', 'butter'],
      option_groups: [],
      conflicts_with_guest: ['dairy'],
    },
  ],
}

const names = () => screen.getAllByRole('heading', { level: 3 }).map((h) => h.textContent)

describe('MenuBrowser', () => {
  test('category tabs, search and "fits my profile" narrow the dishes', () => {
    render(<MenuBrowser menu={menu} onChoose={vi.fn()} />)
    expect(names()).toEqual(['Latte', 'Butter Croissant'])
    fireEvent.click(screen.getByRole('button', { name: 'Bakery and cakes' }))
    expect(names()).toEqual(['Butter Croissant'])
    fireEvent.click(screen.getByRole('button', { name: 'All' }))
    fireEvent.change(screen.getByLabelText('Search the menu'), { target: { value: 'espresso' } })
    expect(names()).toEqual(['Latte'])
    fireEvent.change(screen.getByLabelText('Search the menu'), { target: { value: '' } })
    fireEvent.click(screen.getByLabelText('Fits my profile'))
    expect(names()).toEqual(['Latte'])
  })

  test('a card opens the options sheet for its dish', () => {
    const onChoose = vi.fn()
    render(<MenuBrowser menu={menu} onChoose={onChoose} />)
    fireEvent.click(screen.getAllByRole('button', { name: 'Choose options' })[0] as HTMLElement)
    expect(onChoose).toHaveBeenCalledWith(latte)
    expect(screen.getByRole('button', { name: 'Add to cart' })).toBeInTheDocument()
  })

  test('"Matches my tastes" hides dishes with a soft note, and liked ones say so', () => {
    const sweet = { ...latte, id: 90, name: 'Honey Cake', taste_notes: ['over your 20 SAR budget'] }
    const loved = { ...latte, id: 91, name: 'Mocha', liked: true }
    const tasteMenu = { ...menu, items: [sweet, loved] }
    render(<MenuBrowser menu={tasteMenu} onChoose={vi.fn()} />)
    expect(screen.getByText('Not your usual: over your 20 SAR budget.')).toBeInTheDocument()
    expect(screen.getByText('You like this')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Matches my tastes'))
    expect(names()).toEqual(['Mocha'])
  })
})
