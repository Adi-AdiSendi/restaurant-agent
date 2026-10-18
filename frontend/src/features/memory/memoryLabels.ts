import type { Preference, PreferenceKind } from '../../api/types'

/** The panel's sections, in order, with plain labels. */
export const GROUPS: [PreferenceKind, string][] = [
  ['allergy', 'Allergies'],
  ['diet', 'Diet'],
  ['budget', 'Budget'],
  ['spice', 'Spice'],
  ['calories', 'Daily calorie goal'],
  ['like', 'Likes'],
  ['dislike', 'Dislikes'],
  ['day_dislike', 'On certain days'],
]

const title = (word: string) => word.charAt(0).toUpperCase() + word.slice(1)

export function describe(p: Preference): string {
  if (p.kind === 'budget') return `up to ${p.value} SAR per item`
  if (p.kind === 'calories') return `${Number(p.value).toLocaleString('en')} kcal a day (soft)`
  if (p.kind === 'day_dislike') {
    const [day = '', food = ''] = p.value.split(': ')
    return `${title(day)}s: no ${food}`
  }
  return p.value.replace('_', ' ')
}
