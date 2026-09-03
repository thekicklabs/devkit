# React — Feature

**Read when:** building a screen or a feature slice.
**Prereqs:** [design system](patterns/design-system.md) · [data](patterns/data.md) · [state](patterns/state.md)

---

## Feature slice

```
src/features/<name>/
  api.ts          typed request functions
  hooks.ts        useX() query + mutation hooks
  schemas.ts      Zod for what the user types
  wire.ts         Zod for what the server sends, parsed at the api.ts boundary
  components/     feature-local components
  <Name>Page.tsx  the screen
```

**Flat files, not directories, until a file gets long enough to hurt.** Shared wire
entities live in `src/types/index.ts` rather than a per-feature `types.ts`: every one of
them is the backend's shape, and a copy per feature is a copy that goes stale.

**There is no barrel.** A feature is imported by its full path
(`@/features/application/hooks`). Reaching *across* features is fine and expected when they
address the same resource.

**`schemas.ts` and `wire.ts` are separate on purpose.** One validates what the user types
and can be strict about business rules; the other validates what the server sends and must
tolerate a half-filled draft. Merging them makes autosave fail on every keystroke.

## Order of work

| # | Step | Read |
| --- | --- | --- |
| 1 | Wire types in `src/types/index.ts`, matched to the backend schema | — |
| 2 | MSW handler + seed data | [data](patterns/data.md) |
| 3 | `api.ts` request functions, responses parsed | [data](patterns/data.md) |
| 4 | Query/mutation hooks | [data](patterns/data.md) · [state](patterns/state.md) |
| 5 | Zod schema in `schemas.ts`, if there's a form | [forms](patterns/forms.md) |
| 6 | Translation keys in the feature's namespace | [i18n](patterns/i18n.md) |
| 7 | Components — primitives first, then the screen | [design system](patterns/design-system.md) |
| 8 | Route + guard | [routing](patterns/routing.md) |
| 9 | Tests | [testing](testing.md) |

Data before UI. A screen built against literals gets rewritten when the hook arrives.

## Components

Build the primitive in `src/components/ui/` before the screen that needs it, and test it
there. A variant belongs in CVA, not in a `className` conditional at the call site.

Every view renders loading, error, and empty states — [data](patterns/data.md).

## Accessibility, as you go

Label every control (via `FormField`) · visible focus ring on every interactive element ·
landmarks (`nav`/`main`/`header`) · keyboard-reachable in DOM order · icon-only buttons get an
accessible name. Retrofitting a11y costs more than doing it inline.

## Responsiveness

CSS only. No `window.innerWidth` listeners, no grid strings computed in JS.

## Before you say done

```bash
npm run lint && npm run typecheck && npm run test && npm run build
```

Plus: seen working in `npm run dev` · **light and dark both checked** · resized through the
breakpoints.

**See also:** [testing](testing.md) · [review](review.md)
