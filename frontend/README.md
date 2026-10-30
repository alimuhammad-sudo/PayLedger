# Frontend

Next.js 16 (App Router, TypeScript), Mantine 9 components and charts, TanStack Query.

```bash
npm install
cp .env.example .env.local     # API_ORIGIN=http://localhost:8050
npm run dev -- -p 3050
```

## How it talks to the backend

The browser only calls `/api/*` on this app's own origin. `next.config.ts` rewrites those
requests to `API_ORIGIN` (the FastAPI backend). Because of that:

- the session cookie is first-party and `httpOnly`, so page scripts never see it;
- the backend needs no CORS configuration;
- `API_ORIGIN` is read on the server, so changing it does not need a client rebuild.

## Structure

```
src/app/            routes; (main)/ is everything behind sign-in
src/components/     screens (overview, people, person, payroll) and shared pieces
src/lib/api.ts      fetch wrapper and error type (field errors from the API)
src/lib/queries.ts  TanStack Query hooks; one mutation helper refreshes lists and analytics
src/lib/money.ts    formatting of integer minor units
src/lib/url-state   filters, sort and page kept in the URL
```

## Scripts

| | |
|---|---|
| `npm test` | Vitest + Testing Library |
| `npm run lint` / `npm run typecheck` | ESLint / TypeScript |
| `npm run build` | production build |
