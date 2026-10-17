# frontend

React + Vite + strict TypeScript chat UI with the Foodics brand (ADR 0015).
Built to `dist/`. Locally FastAPI serves it from the same origin; deployed,
Netlify serves it and proxies `/api` to the backend (`../netlify.toml`).

- Entry point: `src/main.tsx`; `src/App.tsx` waits for the server, checks the
  session and shows login or chat.
- `src/api/`: the only code that calls the backend (`client.ts`; a cart or
  order error keeps its `detail.code`), and payload types that mirror the
  Pydantic models (`types.ts`, `menuTypes.ts`, `cartTypes.ts`).
- `src/features/startup/`: polls `/api/health` while the free backend wakes
  up ("Starting the server"), gives up after 2 minutes with a retry button.
- `src/features/login/`: username + 4-digit PIN.
- Routes (React Router, ADR 0021) in `src/App.tsx`, after the startup gate
  and login: `/` restaurants, `/r/:slug` one restaurant, `/checkout`,
  `/orders`, `/orders/:id`; anything else goes back to `/`.
- `src/features/shell/`: `AppShell`, the header on every page (logo, app
  name, Restaurants and Orders links, cart button, user, Log out). It holds
  `CartProvider`.
- `src/features/restaurants/`: the home page grid, from `/api/restaurants`.
- `src/features/menu/`: `MenuPage` for `/r/:slug`: the menu (`MenuBrowser`:
  category tabs, search, "Fits my profile"), and tabs for the chat and the
  memory panel. `ItemSheet` configures a dish (`choice.ts` keeps the rules
  and the live price, for display only), and `useAddLine` turns a 409 into a
  plain question (`AddConfirm`) that only the guest's answer resends.
- `src/features/cart/`: `CartProvider` holds the server's cart (every cart
  call returns the whole cart); `CartButton`, `CartDrawer`, `CartLineRow`.
- `src/features/orders/`: `CheckoutPage` (pickup or dine-in, pay at the
  counter, asks again on a conflict), `OrdersPage`, `OrderPage` (reloads the
  status until ready).
- `src/features/chat/`: `ChatPanel` (New chat, messages, item cards,
  composer, suggestions). State is a pure reducer (`chatReducer.ts`) driven by
  `useChat.ts`; a chat starts at the URL's restaurant, and another restaurant
  starts a new one (only the latest start counts). Cards render only from
  backend item data: allergens are always visible, may-contain warnings are
  highlighted, and `ItemOptions` lists every option group with each option's
  allergens, striking through options that break the guest's saved
  allergies or diet.
- `src/features/memory/`: "What I remember about you", from `/api/preferences`,
  refreshed after each reply. Old facts are struck through. Pages (`menu`)
  compose features; features do not import each other otherwise.
- `netlify/functions/keep-awake.mts`: Netlify scheduled function that pings
  the backend's `/api/health` on Render directly every 10 minutes so the free
  backend stays awake. A test keeps its URL in sync with `../netlify.toml`.
- `src/theme.css`: brand tokens as CSS variables. Components use CSS modules.
- Dev server proxies `/api` to `http://localhost:8000`.

## Run

```
npm install
npm run dev
```

## Checks

```
npm run lint && npm run typecheck && npm test
```
