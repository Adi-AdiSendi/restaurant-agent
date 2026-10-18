import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, test, vi } from 'vitest'

import type { Preference, PreferenceVocabulary } from '../../api/types'
import { mockFetch } from '../../test/fetchMock'
import { LABELS } from '../memory/memoryLabels'
import PreferencesPage from './PreferencesPage'

const row = (id: number, kind: Preference['kind'], value: string, status = 'active') =>
  ({
    id,
    kind,
    value,
    status: status as Preference['status'],
    is_hard: kind === 'allergy' || kind === 'diet',
    superseded_by: null,
    created_at: '2026-10-18T09:00:00Z',
  }) satisfies Preference

const VOCAB: PreferenceVocabulary = {
  allergens: ['gluten', 'peanut', 'tree_nut'],
  diets: ['vegetarian', 'vegan'],
  spice_levels: ['none', 'mild', 'medium', 'hot'],
  weekdays: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
  calories_min: 800,
  calories_max: 6000,
}

const SAVED = [
  row(1, 'allergy', 'peanut'),
  row(7, 'diet', 'vegan'),
  row(2, 'spice', 'mild'),
  row(3, 'dislike', 'pickles'),
  row(4, 'day_like', 'friday: fish'),
  row(5, 'spice', 'hot', 'superseded'),
]

const show = (routes: Parameters<typeof mockFetch>[0] = {}) => {
  const fetchMock = mockFetch({
    'GET /api/preferences': { body: SAVED },
    'GET /api/preferences/vocabulary': { body: VOCAB },
    ...routes,
  })
  render(<PreferencesPage onUnauthorized={vi.fn()} />)
  return fetchMock
}

const sent = (fetchMock: ReturnType<typeof mockFetch>, key: string) =>
  fetchMock.mock.calls
    .filter(([url, init]) => `${init?.method ?? 'GET'} ${String(url)}` === key)
    .map(([, init]) => JSON.parse(String(init?.body ?? 'null')) as unknown)

describe('PreferencesPage', () => {
  test('shows every saved fact in its section, and the old ones struck through', async () => {
    show()
    expect(await screen.findByRole('checkbox', { name: 'Peanut' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: 'Tree nut' })).not.toBeChecked()
    expect(screen.getAllByText('always enforced')).toHaveLength(2)
    const spice = screen.getByRole('group', { name: 'Spice' })
    expect(within(spice).getByRole('radio', { name: 'Mild' })).toBeChecked()
    expect(screen.getByText('pickles')).toBeInTheDocument()
    expect(screen.getByText('Fridays: fish')).toBeInTheDocument()
    expect(screen.getByText('hot').tagName).toBe('S')
  })

  test('has a section for every kind the chat can store (ADR 0026)', async () => {
    show()
    await screen.findByRole('checkbox', { name: 'Peanut' })
    for (const label of Object.values(LABELS)) expect(screen.getByText(label)).toBeInTheDocument()
  })

  test('loosening the diet asks first', async () => {
    const fetchMock = show({ 'PATCH /api/preferences/7': { body: SAVED } })
    fireEvent.click(await screen.findByRole('radio', { name: 'Vegetarian' }))
    expect(screen.getByRole('alertdialog')).toHaveTextContent('from vegan to vegetarian')
    expect(sent(fetchMock, 'PATCH /api/preferences/7')).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Change it' }))
    await expect
      .poll(() => sent(fetchMock, 'PATCH /api/preferences/7'))
      .toEqual([{ value: 'vegetarian' }])
  })

  test('a new spice level replaces the old one, as a correction in the chat would', async () => {
    const fetchMock = show({ 'PATCH /api/preferences/2': { body: [row(6, 'spice', 'hot')] } })
    fireEvent.click(await screen.findByRole('radio', { name: 'Hot' }))
    expect(await screen.findByRole('radio', { name: 'Hot' })).toBeChecked()
    expect(sent(fetchMock, 'PATCH /api/preferences/2')).toEqual([{ value: 'hot' }])
  })

  test('adds a dislike and a day rule from the forms', async () => {
    const fetchMock = show({ 'POST /api/preferences': { status: 201, body: SAVED } })
    const box = await screen.findByRole('textbox', { name: 'Add to dislikes' })
    fireEvent.change(box, { target: { value: 'olives' } })
    fireEvent.submit(box)
    const food = screen.getByRole('textbox', { name: 'Days you avoid: food' })
    fireEvent.change(screen.getByRole('combobox', { name: 'Days you avoid: day' }), {
      target: { value: 'monday' },
    })
    fireEvent.change(food, { target: { value: 'meat' } })
    fireEvent.submit(food)
    await screen.findByRole('checkbox', { name: 'Peanut' })
    await expect
      .poll(() => sent(fetchMock, 'POST /api/preferences'))
      .toEqual([
        { kind: 'dislike', value: 'olives' },
        { kind: 'day_dislike', value: 'monday: meat' },
      ])
  })

  test('removing an allergy asks first, and keeping it changes nothing', async () => {
    const fetchMock = show({ 'DELETE /api/preferences/1': { body: SAVED.slice(1) } })
    fireEvent.click(await screen.findByRole('checkbox', { name: 'Peanut' }))
    const dialog = screen.getByRole('alertdialog')
    expect(dialog).toHaveTextContent('Remove your peanut allergy?')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Keep it' }))
    expect(sent(fetchMock, 'DELETE /api/preferences/1')).toHaveLength(0)

    fireEvent.click(screen.getByRole('checkbox', { name: 'Peanut' }))
    fireEvent.click(screen.getByRole('button', { name: 'Remove' }))
    expect(await screen.findByRole('checkbox', { name: 'Peanut' })).not.toBeChecked()
  })

  test("shows the server's reason when a value is refused", async () => {
    const detail = { code: 'invalid_preference', message: 'calories must be a daily goal' }
    show({ 'POST /api/preferences': { status: 422, body: { detail } } })
    const goal = await screen.findByRole('spinbutton', { name: 'Daily calorie goal in kcal' })
    fireEvent.change(goal, { target: { value: '100' } })
    fireEvent.submit(goal)
    expect(await screen.findByRole('alert')).toHaveTextContent('calories must be a daily goal')
  })
})
