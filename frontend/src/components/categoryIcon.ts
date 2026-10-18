// Matched against the category slug, first hit wins; anything else gets a plate.
const ICONS: [string, string][] = [
  ['coffee', '☕'],
  ['tea', '🍵'],
  ['breakfast', '🍳'],
  ['bakery', '🥐'],
  ['burger', '🍔'],
  ['side', '🍟'],
  ['shake', '🥤'],
  ['drink', '🥤'],
  ['dessert', '🍰'],
  ['soup', '🍜'],
  ['noodle', '🍜'],
  ['wok', '🥢'],
  ['wrap', '🌯'],
  ['shawarma', '🌯'],
  ['grill', '🍢'],
  ['fish', '🐟'],
  ['sea', '🦐'],
  ['bowl', '🥗'],
  ['pasta', '🍝'],
  ['starter', '🥟'],
]

export function categoryIcon(category: string): string {
  return ICONS.find(([word]) => category.includes(word))?.[1] ?? '🍽️'
}
