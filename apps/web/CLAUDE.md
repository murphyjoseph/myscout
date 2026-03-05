# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this app.

## Overview

Next.js 16 (App Router) dashboard for browsing, filtering, and acting on scored job listings. Single-user, local-only — no auth, no deployment.

**This app must never be deployed or exposed to a network.** See the root `CLAUDE.md` for the full list of security items that must be resolved before any deployment. If asked to add deployment configs, push back and reference those requirements first.

## Commands

```bash
pnpm dev              # start dev server at localhost:3000
pnpm build            # production build
npx tsc --noEmit      # type-check only
```

## Stack

- **Next.js 16** with App Router — file-based routing under `src/app/`
- **Chakra UI v3** — uses `createSystem`/`defineConfig` API, NOT the v2 `extendTheme` pattern
- **TanStack Query v5** — all client-side data fetching uses `useQuery`/`useMutation`
- **next-themes** — color mode, integrated with Chakra's `ThemeProvider`
- **pg** — raw SQL queries to Postgres, no ORM

## Frontend Architecture

### Core Principle
Separate logic from rendering so each piece is testable in isolation. If you can't test display logic without mounting a component or mocking a hook, the separation is wrong.

### Dependency Direction
Specific code depends on general code, never the reverse.
- `lib/` is the general-purpose layer — any part of the app can import from it
- Features are isolated from each other — no feature imports from a sibling feature
- Features don't trigger framework side effects (routing, toasts). They fire callbacks — the consuming page handles consequences.
- Prefer duplication over premature sharing. Don't extract to shared until 2-3 concrete uses exist.

### Separation of Concerns

**When a component fetches data or has loading/empty/error states:**

| Concern    | Responsibility                               | Testable without              |
|------------|----------------------------------------------|-------------------------------|
| Controller | Fetches data, manages state, calls presenter | Rendering                     |
| Presenter  | Pure function: raw data → view contract      | Everything (plain assertions) |
| View       | Renders from props, fires callbacks          | Hooks, data fetching          |

**When it's simple** — static component, single-field form with no API, pure display with no states — skip the separation entirely.

### View Contracts
Presenters return a contract with four sections:
- **`renderAs`** — which state to show (`'loading' | 'empty' | 'error' | 'content'`)
- **`display`** — formatted, render-ready strings and labels
- **`instructions`** — boolean flags (`showError`, `disableSubmit`)
- **`effects`** — callbacks the view can fire (`onRetry`, `onSubmit`)

### API Layer
Feature code never calls `fetch()` directly. Wrap API calls in `src/lib/api/` with typed functions. Wire them into TanStack Query as hooks. Functions that can fail return a Result type — `{ success, data }` or `{ success, error }`. Never throw for expected failures.

## Architecture

```
src/
  app/
    layout.tsx                   Root layout, wraps children in Providers
    page.tsx                     Redirects / → /jobs
    jobs/
      page.tsx                   Imports jobs-list feature
      [id]/page.tsx              Imports job-detail feature
    api/
      jobs/
        route.ts                 GET /api/jobs — list with filters
        [id]/
          route.ts               GET /api/jobs/:id — detail + variants
          action/route.ts        PUT /api/jobs/:id/action — update status/notes
  features/
    jobs-list/                   Job list feature (colocated)
      jobs-list.tsx              Wiring layer (controller → view)
      presenter.ts               Pure data → view contract
      view.tsx                   Pure render component
    job-detail/                  Job detail feature (colocated)
      job-detail.tsx             Wiring layer
      presenter.ts               Pure data → view contract
      view.tsx                   Pure render component
  lib/
    api/
      jobs.ts                    Typed API gateway functions
    db.ts                        Postgres connection pool (server-side only)
    types.ts                     Shared TypeScript interfaces
  components/
    providers.tsx                ChakraProvider + QueryClientProvider
```

## Patterns

### Database access
Route handlers query Postgres directly via `src/lib/db.ts`. Use parameterized queries (`$1`, `$2`) — never interpolate values into SQL strings. The `query<T>()` helper returns typed rows.

### Providers
`providers.tsx` is a `"use client"` component that composes both Chakra and TanStack Query providers. The QueryClient uses the `isServer` check pattern from TanStack docs to avoid shared state between requests.

### SQL conventions
- Always use `LATERAL JOIN` for "latest score" queries (avoids N+1)
- `COALESCE(ja.status, 'NEW')` — jobs without an action row default to NEW
- Filters build a dynamic WHERE clause with parameterized `$N` placeholders

## LOCAL-ONLY tradeoffs
When adding new endpoints or features, mark intentional security shortcuts with `// LOCAL-ONLY:` comments. Current ones: hardcoded DB credentials in `db.ts`, no auth on mutation endpoints. Job description HTML is sanitized via DOMPurify in the presenter layer.
