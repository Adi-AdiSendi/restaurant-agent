import { render, screen } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { Preference } from '../../api/types'
import { mockFetch } from '../../test/fetchMock'
import MemoryPanel from './MemoryPanel'

const row = (id: number, kind: Preference['kind'], value: string, status: Preference['status']) =>
  ({
    id,
    kind,
    value,
    status,
    is_hard: kind === 'allergy' || kind === 'diet',
    superseded_by: null,
    created_at: '2026-10-17T09:00:00Z',
  }) satisfies Preference

describe('MemoryPanel', () => {
  test('shows active facts, marks hard ones as enforced, strikes through old ones', async () => {
    mockFetch({
      'GET /api/preferences': {
        body: [
          row(3, 'spice', 'mild', 'active'),
          row(2, 'allergy', 'tree_nut', 'active'),
          row(1, 'spice', 'hot', 'superseded'),
        ],
      },
    })
    render(<MemoryPanel refreshKey={0} onUnauthorized={vi.fn()} />)
    expect(await screen.findByText('tree nut')).toBeInTheDocument()
    expect(screen.getByText('mild')).toBeInTheDocument()
    expect(screen.getByText('always enforced')).toBeInTheDocument()
    expect(screen.getByText('hot').tagName).toBe('S')
  })

  test('invites the guest to share preferences when nothing is stored', async () => {
    mockFetch({ 'GET /api/preferences': { body: [] } })
    render(<MemoryPanel refreshKey={0} onUnauthorized={vi.fn()} />)
    expect(await screen.findByText(/Nothing yet/)).toBeInTheDocument()
  })

  test('a lost session sends the guest back to login', async () => {
    mockFetch({ 'GET /api/preferences': { status: 401, body: { detail: 'Please log in.' } } })
    const onUnauthorized = vi.fn()
    render(<MemoryPanel refreshKey={0} onUnauthorized={onUnauthorized} />)
    await vi.waitFor(() => expect(onUnauthorized).toHaveBeenCalled())
  })

  test('shows day rules, the calorie goal and today against it', async () => {
    mockFetch({
      'GET /api/preferences': {
        body: [
          row(5, 'day_dislike', 'friday: meat', 'active'),
          row(6, 'calories', '1800', 'active'),
        ],
      },
      'GET /api/preferences/today': { body: { weekday: 'friday', kcal: 650 } },
    })
    render(<MemoryPanel refreshKey={0} onUnauthorized={vi.fn()} />)
    expect(await screen.findByText('Fridays: no meat')).toBeInTheDocument()
    expect(screen.getByText('1,800 kcal a day (soft)')).toBeInTheDocument()
    const progress = await screen.findByRole('progressbar')
    expect(progress).toHaveAttribute('value', '650')
    expect(screen.getByText(/Today: 650 of 1,800 kcal ordered/)).toBeInTheDocument()
  })
})
