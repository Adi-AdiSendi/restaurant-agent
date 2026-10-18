import { fireEvent, render, screen } from '@testing-library/react'
import { expect, test, vi } from 'vitest'

import { latte } from '../../test/cards'
import MessageBubble from './MessageBubble'

test('a recommended dish in the chat opens the same options sheet as the menu', () => {
  const onChoose = vi.fn()
  const message = {
    id: 1,
    role: 'assistant' as const,
    text: 'Try this.',
    items: [latte],
    actions: [],
  }
  render(<MessageBubble message={message} onChoose={onChoose} />)
  fireEvent.click(screen.getByRole('button', { name: 'Choose options' }))
  expect(onChoose).toHaveBeenCalledWith(latte)
})

test('without a sheet to open, cards have no button', () => {
  const message = {
    id: 1,
    role: 'assistant' as const,
    text: 'Try this.',
    items: [latte],
    actions: [],
  }
  render(<MessageBubble message={message} />)
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})
