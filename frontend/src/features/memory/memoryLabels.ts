import type { Preference, PreferenceKind } from '../../api/types'

/** A plain label for every kind, in panel order. A Record, so a new kind
 * without a label (and so without a Preferences section) fails to compile. */
export const LABELS: Record<PreferenceKind, string> = {
  allergy: 'Allergies',
  diet: 'Diet',
  budget: 'Budget per dish',
  spice: 'Spice',
  calories: 'Daily calorie goal',
  like: 'Likes',
  dislike: 'Dislikes',
  day_dislike: 'Days you avoid',
  day_like: 'Days you want',
}

export const GROUPS = Object.entries(LABELS) as [PreferenceKind, string][]

const title = (word: string) => word.charAt(0).toUpperCase() + word.slice(1)

/** A stored value as a plain label: "tree_nut" -> "Tree nut". */
export const plainLabel = (value: string) => title(value.replace('_', ' '))

export function describe(p: Preference): string {
  if (p.kind === 'budget') return `up to ${p.value} SAR per item`
  if (p.kind === 'calories') return `${Number(p.value).toLocaleString('en')} kcal a day (soft)`
  if (p.kind === 'day_dislike' || p.kind === 'day_like') {
    const [day = '', food = ''] = p.value.split(': ')
    return `${title(day)}s: ${p.kind === 'day_dislike' ? 'no ' : ''}${food}`
  }
  return p.value.replace('_', ' ')
}
