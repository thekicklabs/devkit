---
name: react
description: Vite + React + TanStack Query + Zustand + React Hook Form/Zod + Tailwind/DaisyUI — feature slices, four homes for state, MSW-first data, design system
route: React frontend
requires: [typescript]
---
# React — router

**Read when:** any task touching the frontend.
**Prereq:** [`../typescript/AGENTS.md`](../typescript/AGENTS.md) · `../workflow.md`

Vite + `@vitejs/plugin-react` · TypeScript `strict`, alias `@/*` · Tailwind v4 + DaisyUI 5 +
`class-variance-authority` + `tailwind-merge` · React Router v7 · TanStack Query v5 · Zustand v5 ·
React Hook Form 7 + Zod 4 · `lucide-react` · MSW 2 (browser in dev, node in tests) · Vitest +
Testing Library + jsdom · Playwright for E2E · react-i18next.

## Layout

```
src/
  app/              App.tsx · router.tsx · ThemeProvider.tsx · routes/
  components/       ui/ (primitives) · layout/ · shared domain widgets
  features/<name>/  api.ts · hooks.ts · schemas.ts · wire.ts · components/ · <Name>Page.tsx
  lib/              api.ts · queryClient.ts · cn.ts · format.ts · constants.ts · i18n.ts
  locales/<lang>/   <namespace>.json
  mocks/            handlers.ts · seed.ts · browser.ts · server.ts
  stores/           themeStore.ts · uiStore.ts
  styles/           theme.css · globals.css
  test/             setup.ts · render.tsx
  types/            index.ts (wire entities shared across features)
```

## Routing

| Doing… | Read |
| --- | --- |
| Building a screen or feature | [`feature.md`](feature.md) |
| Writing or fixing tests | [`testing.md`](testing.md) |
| Restructuring existing code | [`refactor.md`](refactor.md) |
| Auth, uploads, personal data | [`security.md`](security.md) |
| Slow render, big bundle, refetch storm | [`performance.md`](performance.md) |
| Chasing a bug | [`debug.md`](debug.md) |
| Reviewing a diff | [`review.md`](review.md) |

**Patterns** (read the ones your task touches):
[design system](patterns/design-system.md) · [state](patterns/state.md) ·
[forms](patterns/forms.md) · [data](patterns/data.md) · [routing](patterns/routing.md) ·
[i18n](patterns/i18n.md) · [feature flags](patterns/feature-flags.md)

## Non-negotiables

1. **Semantic theme slots only — never a raw hex** (`bg-base-100`, `text-base-content`).
2. **No raw DaisyUI class strings outside `src/components/ui/`** — features use the wrappers.
3. **The URL is the navigation state.** No `useState` screen switching — [routing](patterns/routing.md).
4. **Server state lives in Query, never copied into `useState`** — [state](patterns/state.md).
5. **MSW is the default data source; the API is the authority.** `npm run dev` runs on mocks
   so frontend work never blocks on a backend; `VITE_ENABLE_MSW=false` swaps in the real API
   through the same-origin `/api` proxy. When a handler and the API disagree, the API is
   right and the handler is stale.
6. **No user-facing literal in a component** — every string through `t()`, including
   `aria-label`, placeholders and titles — [i18n](patterns/i18n.md).
7. **Restraint is the default** — one frame around one thing, a glyph before a badge, terse
   where terseness loses nothing — [design system](patterns/design-system.md#restraint).
8. **A control says what it does, once.** Decisions at the foot of the work, one primary per
   surface, an action a record cannot take is not offered on it —
   [design system](patterns/design-system.md#acting-on-a-record).
9. **Explaining technical decisions in the UI is madness.** Copy is written for the user,
   not the engine: no status codes, no enum values, no schema vocabulary.

## Before you say done

```bash
npm run lint && npm run typecheck && npm run test && npm run build
```

Plus: seen working in `npm run dev` · **light and dark both checked** · resized through the
project's breakpoints.
