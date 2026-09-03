# TypeScript — Testing

**Read when:** writing or changing tests; before declaring TypeScript work done.

Vitest. Testing Library where there is a DOM. Tests pass before "done" — paste the run.

---

## Setup

One `src/test/setup.ts`, wired in `vite.config.ts` / `vitest.config.ts`: `jest-dom`
matchers, `cleanup()`, any mock server lifecycle, timezone pinned with
`env: { TZ: '…' }` so a date rendered on a laptop and in CI reads the same. `globals: true`
so `describe`/`it`/`expect` need no import.

Render through a shared helper (`src/test/render.tsx`) that mounts the providers the app
mounts. A component rendered bare misses a provider and fails for the wrong reason.

## How to query

- **By role and accessible name first.** `getByRole('button', { name: /submit/i })` tests
  what a user and a screen reader can find.
- `getByLabelText` for form controls — it also proves the label association.
- `getByTestId` only when nothing else identifies the element.
- **`findBy*` for anything after an async step.** Never `waitFor` around a bare `getBy`.
- **A word the screen says twice is queried inside the row that says it**: find the row by
  something unique, `within(row.closest('tr'))`, then query. `findByText(/submitted/i)` that
  works today fails as "multiple elements" the day a sibling gains the word.

## What a test must not be

- **A snapshot.** It passes until it doesn't, then everyone re-records it.
- **Coupled to implementation** — asserting on class names, internal state, or call counts
  while behaviour is identical.
- **Asserting the formatter agrees with itself** — write the expected date/number string
  literally as a reader sees it; never compute it by calling the formatter under test.

## Mocking the network

Override handlers per test, scoped by an `afterEach` reset — never a global mutation. Test
the error path by overriding to a 500: it is the state most likely to be broken and least
likely to be looked at. An unhandled request should **fail** the test
(`onUnhandledRequest: 'error'`) so a typo'd path is caught immediately, not as `undefined`
data.

## Running

```bash
npm run test -- path/to/file.test.ts -t "test name"
npm run test                                       # the suite, before "done"
```

**See also:** `../react/testing.md` when installed
