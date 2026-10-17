// Two restaurants, as GET /api/restaurants returns them, and one menu.
import { latte } from './cards'

export const restaurants = {
  'GET /api/restaurants': {
    body: [
      {
        id: 1,
        slug: 'corner-table',
        name: 'Corner Table',
        cuisine: 'International casual',
        tagline: 'T.',
        accent_color: '#440099',
        categories: ['starters'],
      },
      {
        id: 2,
        slug: 'golden-dragon',
        name: 'Golden Dragon',
        cuisine: 'Chinese',
        tagline: 'T.',
        accent_color: '#d4a017',
        categories: ['wok_dishes'],
      },
    ],
  },
}

const dragon = restaurants['GET /api/restaurants'].body[1]

/** Golden Dragon's menu: one latte, enough to render the page. */
export const dragonMenu = {
  'GET /api/restaurants/golden-dragon/menu': {
    body: { restaurant: dragon, items: [{ ...latte, category: 'wok_dishes' }] },
  },
}
