import type { Card } from '../../api/menuTypes'

/** One-click add for dish cards and menu blocks; `added` is the dish just added, if any. */
export interface QuickAdd {
  add: (item: Card) => void
  added: number | null
}

/** A dish can be added in one click when no choice is needed and nothing conflicts. */
export function canQuickAdd(item: Card): boolean {
  return item.option_groups.every((g) => g.min_choices === 0) && !item.conflicts_with_guest.length
}
