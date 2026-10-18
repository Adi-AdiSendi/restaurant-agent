import { fireEvent, render } from '@testing-library/react'
import { expect, test } from 'vitest'

import { categoryIcon } from './categoryIcon'
import DishPhoto from './DishPhoto'

test('a photo loads both sizes from the menu folder', () => {
  const { container } = render(<DishPhoto photo="golden-dragon/mapo-tofu" icon="🥢" />)
  const img = container.querySelector('img')
  expect(img).toHaveAttribute('src', '/menu/golden-dragon/mapo-tofu-640.webp')
  expect(img?.getAttribute('srcset')).toContain('/menu/golden-dragon/mapo-tofu-320.webp 320w')
  expect(img).toHaveAttribute('alt', '')
})

test('no photo, or one that fails to load, shows the icon', () => {
  const none = render(<DishPhoto photo={null} icon="🍔" />)
  expect(none.container.querySelector('img')).toBeNull()
  expect(none.container).toHaveTextContent('🍔')

  const broken = render(<DishPhoto photo="stack-and-smash/gone" icon="🍟" />)
  fireEvent.error(broken.container.querySelector('img') as HTMLImageElement)
  expect(broken.container.querySelector('img')).toBeNull()
  expect(broken.container).toHaveTextContent('🍟')
})

test('category icons match the category slug, with a plate for anything else', () => {
  expect(categoryIcon('coffee')).toBe('☕')
  expect(categoryIcon('noodles_and_rice')).toBe('🍜')
  expect(categoryIcon('from_the_grill')).toBe('🍢')
  expect(categoryIcon('mystery')).toBe('🍽️')
})
