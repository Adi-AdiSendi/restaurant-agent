# 0021: Client routing with React Router

- Status: Accepted
- Date: 2026-10-17

## Context
v1 has one screen, switched by state in `App.tsx`. v2 adds restaurants,
menus, the cart, checkout, orders, a personal page and a staff dashboard.
Guests expect working links, back buttons and refresh.

## Decision
Use `react-router` (declarative mode, `BrowserRouter`). Netlify already
rewrites unknown paths to `index.html`, and FastAPI serves the SPA locally,
so deep links work in both places. The startup gate and login stay in front
of the routes.

## Alternatives considered
- Keep view state in `App.tsx`: no dependency, but no URLs, no back button,
  and the file would outgrow its limit.
- A framework with file routing (Next.js, Remix): more than a static SPA needs.

## Consequences
- One new runtime dependency.
- Staff routes are hidden in the UI, but access is enforced by the API.
