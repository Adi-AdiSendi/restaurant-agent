# 0015: Foodics brand for the prototype UI

- Status: Accepted
- Date: 2026-10-17

## Context
The prototype is presented to the Foodics team. A familiar look makes the demo
feel like a Foodics product, but branding should not cost time that belongs to
the agent.

## Decision
- Colours, font and logo follow foodics.com (read from its CSS on 2026-10-17):
  primary `#440099`, accent `#312490`, tint `#EDE9F8`, ink `#2E2D2C`,
  muted `#666666`, info `#78C4DD`, page `#F8F9FA`, line `#E5E7EB`,
  warning background `#FEF3C7`, danger `#EF4444`. Font: IBM Plex Sans.
- Tokens live as CSS variables in one theme file. Components use CSS modules
  that read the variables. No UI framework.
- The logo is a local copy in `frontend/public/`, not hotlinked.
- The header shows the Foodics logo, a fictional restaurant name and
  "Powered by Foodics". Light theme only.

## Alternatives considered
- A neutral custom theme: no brand risk, but less relevant to the reviewers.
- Branding fully as Foodics with no restaurant: blurs that Foodics is the
  platform and the restaurant is its customer.

## Consequences
- Brand assets belong to Foodics and are used for this prototype only.
  Noted in README limitations.
- Dark theme and Arabic (RTL) are out of scope.
