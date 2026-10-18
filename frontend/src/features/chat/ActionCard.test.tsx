import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'

import { oatLatte } from '../../test/carts'
import { addedLatte } from '../../test/chat'
import ActionCard from './ActionCard'

test('an add shows the dish, its choices and what was left out for the guest', () => {
  render(<ActionCard action={addedLatte} />)
  expect(screen.getByText('Added 2 × Latte')).toBeInTheDocument()
  expect(screen.getByText('Oat milk, no sugar')).toBeInTheDocument()
  expect(screen.getByText('Left out sugar, as you prefer.')).toBeInTheDocument()
})

test('a change and a removal say what happened to the line', () => {
  const line = { ...oatLatte, removed: [] }
  render(<ActionCard action={{ kind: 'updated', quantity: 3, line, left_out: [] }} />)
  render(<ActionCard action={{ kind: 'removed', quantity: 2, line, left_out: [] }} />)
  expect(screen.getByText('Changed to 3 × Latte')).toBeInTheDocument()
  expect(screen.getByText('Removed Latte')).toBeInTheDocument()
  expect(screen.queryByText(/as you prefer/)).not.toBeInTheDocument()
})

test('an emptied cart says how many items went', () => {
  render(<ActionCard action={{ kind: 'cleared', quantity: 3, line: null, left_out: [] }} />)
  expect(screen.getByText('Emptied the cart (3 items)')).toBeInTheDocument()
})
