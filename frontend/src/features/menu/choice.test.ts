import { describe, expect, test } from 'vitest'

import { latte } from '../../test/cards'
import {
  chosenConflicts,
  initialChoice,
  linePrice,
  missing,
  toggleOption,
  toggleRemoved,
} from './choice'

const [milk, syrup] = latte.option_groups
if (!milk || !syrup) throw new Error('the latte fixture has two groups')

describe('item sheet choices', () => {
  test('a required single choice starts on the first option that suits the guest', () => {
    expect(initialChoice(latte)).toEqual({ optionIds: [2], removed: [], quantity: 1 })
    expect(linePrice(latte, initialChoice(latte))).toBe('19.00')
  })

  test('a single choice swaps, and cannot be emptied when required', () => {
    const whole = toggleOption(initialChoice(latte), milk, 1)
    expect(whole.optionIds).toEqual([1])
    expect(toggleOption(whole, milk, 1).optionIds).toEqual([1])
    expect(chosenConflicts(latte, whole)).toEqual(['dairy'])
  })

  test('a multiple choice stops at its maximum', () => {
    let choice = initialChoice(latte)
    for (const id of [3, 4, 5]) choice = toggleOption(choice, syrup, id)
    expect(choice.optionIds).toEqual([2, 3, 4])
    choice = toggleOption(choice, syrup, 3)
    expect(choice.optionIds).toEqual([2, 4])
  })

  test('price covers options and quantity', () => {
    const choice = { ...toggleOption(initialChoice(latte), syrup, 3), quantity: 2 }
    expect(linePrice(latte, choice)).toBe('42.00')
  })

  test('missing required choices and removals', () => {
    expect(missing(latte, { optionIds: [], removed: [], quantity: 1 })).toEqual(['Choose a milk'])
    expect(missing(latte, initialChoice(latte))).toEqual([])
    const without = toggleRemoved(initialChoice(latte), 'sugar')
    expect(without.removed).toEqual(['sugar'])
    expect(toggleRemoved(without, 'sugar').removed).toEqual([])
  })
})
