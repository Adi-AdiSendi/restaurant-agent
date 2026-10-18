import { act, render } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, expect, test, vi } from 'vitest'

import { placedOrder } from '../../test/carts'
import OrderView, { REFRESH_MS } from './OrderView'

afterEach(() => {
  vi.useRealTimers()
})

test('leaving while the order loads schedules no reload', async () => {
  vi.useFakeTimers()
  let answer: (r: Response) => void = () => undefined
  const fetchMock = vi.fn(() => new Promise<Response>((resolve) => (answer = resolve)))
  vi.stubGlobal('fetch', fetchMock)
  const { unmount } = render(
    <MemoryRouter>
      <OrderView id={31} />
    </MemoryRouter>,
  )
  unmount()
  // A "preparing" order would normally be reloaded after REFRESH_MS.
  await act(async () => {
    answer(new Response(JSON.stringify(placedOrder)))
    await vi.advanceTimersByTimeAsync(REFRESH_MS * 2)
  })
  expect(fetchMock).toHaveBeenCalledTimes(1)
})
