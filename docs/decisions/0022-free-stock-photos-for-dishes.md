# 0022: Free stock photos for dishes

- Status: Superseded by [0024](0024-openverse-photos-for-dishes.md)
- Date: 2026-10-17

## Context
v2 shows food on cards in the menu and in the chat. About 100 dishes need a
photo. The prototype has no budget for content.

## Decision
- Photos come from Pexels and Unsplash under their free licences.
- A script fetches candidates per dish with a free Pexels API key; the user
  picks one per dish from a contact sheet.
- An import script crops to 4:3 and writes WebP at 320 and 640 px (about
  30 to 50 KB each) under `frontend/public/menu/<restaurant>/`. They are
  committed, so the site never hotlinks.
- `docs/photo-credits.md` names the photographer and source of every photo.
- A missing photo falls back to a cuisine icon on the restaurant's accent
  colour.

## Alternatives considered
- AI-generated photos: one consistent style, but a small cost and images of
  food that does not exist.
- No photos: free and fast, but weak at showing food.

## Consequences
- Styles vary between photos, and a photo shows a similar dish, not ours.
  Cards still take name, price and allergens from the database (0010).
- About 8 MB of images in the repo.
