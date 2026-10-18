# frontend

React + Vite + strict TypeScript chat UI with the Foodics brand (ADR 0015).
Built to `dist/`. Locally FastAPI serves it from the same origin; deployed,
Netlify serves it and proxies `/api` to the backend (`../netlify.toml`).

- Entry point: `src/main.tsx`; `src/App.tsx` waits for the server, checks the
  session and shows login or chat.
- `src/api/`: the only code that calls the backend (`client.ts`; `errors.ts`
  keeps a cart or order error's `detail.code`), and payload types that mirror the
  Pydantic models (`types.ts`, `menuTypes.ts`, `cartTypes.ts`).
- `src/components/`: pieces shared by features: `useModal`, `DishPhoto`
  (the WebP sizes under `public/menu/`, named by the database, with a category
  icon on the restaurant's colour when there is no photo; ADR 0024) and
  `Skeleton` (placeholders while a list loads) and `Storefront` (a
  restaurant's sign, used on the restaurants list and in orders).
- `public/storefronts/`: each restaurant's sign (3:1, supplied by the project
  owner), shown as a banner on the restaurants list, one restaurant per row.
- `public/menu/<restaurant>/`: reviewed Openverse photos, credited in
  `../docs/photo-credits.md`; written by `backend/scripts/photos/`.
- `src/features/startup/`: polls `/api/health` while the free backend wakes
  up ("Starting the server"), gives up after 2 minutes with a retry button.
- `src/features/login/`: username + 4-digit PIN.
- Routes (React Router, ADR 0021) in `src/App.tsx`, after the startup gate
  and login: `/` restaurants, `/r/:slug` one restaurant, `/checkout`,
  `/orders`, `/orders/:id`, `/preferences`; anything else goes back to `/`.
- `src/features/shell/`: `AppShell`, the header on every page (logo, app
  name, Restaurants, Orders and Preferences links, cart button, user, Log out). It holds
  `CartProvider`.
- `src/features/restaurants/`: the home page grid, from `/api/restaurants`.
- `src/features/menu/`: `MenuRoute` keys `MenuPage` by `/r/:slug`, so each
  restaurant starts afresh. `MenuPage` holds the menu (`MenuBrowser`:
  category tabs, search, "Fits my profile"), and tabs for the chat and the
  memory panel. `ItemSheet` configures a dish (`choice.ts` keeps the rules
  and the live price, for display only), and `useAddLine` turns a 409 into a
  plain question (`AddConfirm`) that only the guest's answer resends.
- `src/features/cart/`: `CartProvider` holds the server's cart (every cart
  call returns the whole cart); `CartButton`, `CartDrawer`, `CartLineRow`.
- `src/features/orders/`: `CheckoutPage` (pickup or dine-in, pay at the
  counter, asks again on a conflict) and the chat's `CheckoutCard` share
  `usePlaceOrder`; only the guest's button places an order. `OrdersPage`
  lists `OrderCard`s (the restaurant's sign, dish photos, status, the price
  paid) under the total spent; `OrderPage` keys `OrderView` by the order id
  (it reloads the status until ready) and renders `OrderDetail`, a receipt
  with `StatusSteps`, a photo per dish and the total paid.
- `src/features/chat/`: `ChatPanel` (New chat, messages, item cards,
  composer, suggestions). State is a pure reducer (`chatReducer.ts`) driven by
  `useChat.ts`; a chat starts at the URL's restaurant, and another restaurant
  starts a new one (only the latest start counts). Cards render only from
  backend item data: allergens are always visible, may-contain warnings are
  highlighted, and `ItemOptions` lists every option group with each option's
  allergens, striking through options that break the guest's saved
  allergies or diet. A reply's `actions` render as `ActionCard`s ("Added 2 ×
  Latte", what was left out for the guest's dislikes) or a `CheckoutCard`,
  all from server data. `MenuPage` sets the cart from each reply's `cart`.
- `src/features/voice/`: the mic in the composer (English). `speech.ts` uses
  the browser's recognition where it exists; `record.ts` records a clip for
  `/api/transcribe` elsewhere. The text goes into the box for the guest to
  send, or with the **Auto** toggle (saved in `localStorage`) it is sent at once.
- `src/features/memory/`: "What I remember about you", from `/api/preferences`,
  refreshed after each reply, with an "Edit preferences" link. Old facts are
  struck through (`PastFacts`, also on the Preferences page). Pages (`menu`)
  compose features. A few pieces cross over: the cart context, the chat's
  `ItemCard` on the menu, and the orders `CheckoutCard` in the chat.
- `src/features/preferences/`: `/preferences`, every remembered fact edited
  by hand (ADR 0026): `HardRules` (allergies, removal asks first; diet),
  `SoftLimits` (spice, budget, calorie goal), `FoodTastes` (likes,
  dislikes, days you avoid and want). `usePreferences` loads the facts and
  the allowed values from the server; each edit returns the whole history.
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
