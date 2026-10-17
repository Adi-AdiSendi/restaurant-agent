// What the guest has picked in the item sheet. Pure functions; the server
// prices and checks the line again when it is added, so these only preview.
import type { Card, OptionGroup } from '../../api/menuTypes'

export interface Choice {
  optionIds: number[]
  removed: string[]
  quantity: number
}

const cents = (sar: string) => Math.round(Number(sar) * 100)

/** Required single choices start on their first option that suits the guest. */
export function initialChoice(item: Card): Choice {
  const optionIds = item.option_groups
    .filter((g) => g.min_choices >= 1 && g.max_choices === 1)
    .map((g) => (g.options.find((o) => o.conflicts_with_guest.length === 0) ?? g.options[0])?.id)
    .filter((id): id is number => id !== undefined)
  return { optionIds, removed: [], quantity: 1 }
}

export function toggleOption(choice: Choice, group: OptionGroup, optionId: number): Choice {
  const inGroup = new Set(group.options.map((o) => o.id))
  const picked = choice.optionIds.filter((id) => inGroup.has(id))
  const others = choice.optionIds.filter((id) => !inGroup.has(id))
  let next: number[]
  if (picked.includes(optionId)) {
    // A required single choice cannot be emptied; pick another one instead.
    next =
      group.max_choices === 1 && group.min_choices === 1
        ? picked
        : picked.filter((id) => id !== optionId)
  } else if (group.max_choices === 1) {
    next = [optionId]
  } else {
    next = picked.length < group.max_choices ? [...picked, optionId] : picked
  }
  return { ...choice, optionIds: [...others, ...next] }
}

export function toggleRemoved(choice: Choice, ingredient: string): Choice {
  const removed = choice.removed.includes(ingredient)
    ? choice.removed.filter((r) => r !== ingredient)
    : [...choice.removed, ingredient]
  return { ...choice, removed }
}

/** What still has to be chosen before the dish can be added. */
export function missing(item: Card, choice: Choice): string[] {
  return item.option_groups
    .filter((g) => g.options.filter((o) => choice.optionIds.includes(o.id)).length < g.min_choices)
    .map((g) => `Choose ${g.min_choices === 1 ? 'a' : g.min_choices} ${g.name.toLowerCase()}`)
}

/** Price for the whole quantity, as "19.00". */
export function linePrice(item: Card, choice: Choice): string {
  const options = item.option_groups.flatMap((g) => g.options)
  const extras = options
    .filter((o) => choice.optionIds.includes(o.id))
    .reduce((sum, o) => sum + cents(o.price_delta_sar), 0)
  return (((cents(item.price_sar) + extras) * choice.quantity) / 100).toFixed(2)
}

/** Why the chosen options do not suit the guest; empty if they do. */
export function chosenConflicts(item: Card, choice: Choice): string[] {
  const reasons = item.option_groups
    .flatMap((g) => g.options)
    .filter((o) => choice.optionIds.includes(o.id))
    .flatMap((o) => o.conflicts_with_guest)
  return [...new Set([...item.conflicts_with_guest, ...reasons])]
}
