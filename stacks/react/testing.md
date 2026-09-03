# React — Testing

**Read when:** writing or changing frontend tests; before declaring frontend work done.
**Prereq:** [`../typescript/testing.md`](../typescript/testing.md)

Vitest + Testing Library + jsdom for components and feature flows. Playwright for the
journey. MSW serves both — the same handlers as dev, so tests exercise the real request path.

---

## Setup

`src/test/setup.ts` handles: `jest-dom`, RTL `cleanup()`, the MSW server lifecycle
(`server.resetHandlers()` in `afterEach`), `resetDb()`, `localStorage.clear()`, jsdom stubs
for `matchMedia` / `scrollTo`, and i18n initialised with `en`. New mutable module state needs
resetting there too.

`src/test/render.tsx` mounts QueryClient + Router + theme + i18n providers. Fresh
`QueryClient` per test with `retry: false` — otherwise a failing query retries into a
timeout.

## Override handlers per test

```ts
server.use(http.get('/api/applications/:id', () => HttpResponse.json({ ...seed, submitted: true })))
```

Scoped to the test by the `afterEach` reset. Test the error path by overriding to a 500, and
the error **code** path by overriding to the envelope the API actually sends
(`{ error: { code: 'APPLICATION_NOT_FOUND', … } }`).

## Assert on translated text, not keys

The helper loads `en`. Assert what the user sees (`/submit application/i`), never a key
(`application.submit`). A key on screen is itself a bug the test should catch.

## What must have a test

- Primitives in `src/components/ui/`: each variant, disabled and loading states, and that
  `className` merges.
- Flow tests per feature for every **business rule the UI mirrors** — a gate, a lock, a
  per-step validation. Drive them from the data (`sectionsReopened`, a required count) —
  a test that hardcodes the id or the number reproduces the bug it should catch.
- Unauthenticated access redirects to `/login`; the query error state renders with a working
  retry; an unknown route param redirects somewhere sensible.
- A control that performs two writes: the first is not repeated when the second is refused.

## Playwright

E2E covers **the journey, once** — the golden path end to end, plus deep-linking and
browser-back at each step, which unit tests can't prove. Don't re-test component behaviour in
Playwright; it's slower and flakier for the same assertion.

## Theming

Toggling light/dark is a manual check on every screen, not an assertion — but a component
that hardcodes a hex is caught in [review](review.md).

**See also:** [feature](feature.md) · [data](patterns/data.md) · [forms](patterns/forms.md)
