# 0024: Openly licensed photos from Openverse

- Status: Accepted
- Date: 2026-10-18
- Supersedes: [0022](0022-free-stock-photos-for-dishes.md)

## Context
ADR 0022 planned Pexels and Unsplash photos fetched with a free Pexels API
key. There is no key. About 100 dishes and 6 restaurants need a photo, with
no budget for content, and every photo must be licensed for this use.

## Decision
- Photos come from Openverse, which searches openly licensed images and
  needs no key for light use.
- Only licences that allow changes and commercial use: CC0, the Public
  Domain Mark, CC BY and CC BY-SA. A cropped CC BY-SA photo stays CC BY-SA.
- A script ranks candidates per dish (`backend/scripts/photos/`) and picks
  one. The user reviews every pick on a contact sheet and can swap it for
  an alternate or for no photo.
- An import script crops to 4:3 and writes WebP at 320 and 640 px under
  `frontend/public/menu/<restaurant>/`. They are committed, so the site never
  hotlinks.
- `docs/photo-credits.md` names the title, creator, licence and source of
  every photo, and says it was cropped and resized.
- The item and restaurant records name their photo (`photo` columns), so
  the UI takes it from the database like every other dish detail (0010).
- No photo, or one that fails to load, shows a category icon on the
  restaurant's accent colour.

## Alternatives considered
- Pexels or Unsplash by hand: better photos, but about 110 manual downloads.
- AI-generated photos: one consistent style, but a small cost and images of
  food that does not exist.
- Icons only: free and fast, but weak at showing food.

## Consequences
- Quality and style vary, and some dishes may have no good match and keep
  the icon. A photo shows a similar dish, not ours.
- About 6 MB of images in the repo.
- Credits must stay in step with the files; a test checks it.
