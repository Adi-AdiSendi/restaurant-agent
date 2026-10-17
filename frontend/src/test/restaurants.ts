// Two restaurants, as GET /api/restaurants returns them.
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
