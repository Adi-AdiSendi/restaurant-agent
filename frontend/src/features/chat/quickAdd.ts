import type { Card } from '../../api/menuTypes'

/** One-click add for dish cards and menu blocks. */
export interface QuickAdd {
  add: (item: Card) => void
  /** The dish just added, for a moment of "Added" feedback. */
  added: number | null
  /** The dish being added; its button waits, so a double click adds one. */
  pending: number | null
}

/** One click only when there is nothing to choose or notice: no options or removable
 * ingredients (the sheet shows those), no conflict and no trace warning for the guest. */
export function canQuickAdd(item: Card): boolean {
  return (
    item.option_groups.length === 0 &&
    item.removable.length === 0 &&
    item.conflicts_with_guest.length === 0 &&
    item.may_contain_warnings.length === 0
  )
}

/** What a screen reader hears for the Add button, including that the add worked. */
export function addLabel(item: Card, quickAdd: QuickAdd): string {
  return quickAdd.added === item.id
    ? `${item.name} added to the cart`
    : `Add ${item.name} to the cart`
}
