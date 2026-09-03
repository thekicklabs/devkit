# Pattern — routing

**Read when:** adding a screen, or anything that changes what's on screen.

React Router v7. **The URL is the navigation state** — real URLs, deep links, a working back
button, and state that survives a refresh.

---

## Rules

- **No conditional screen rendering off component state.** If it changes what the user sees
  as a "page", it's a route.
- **Filters and view selection go in the query string** (`useSearchParams`), through one
  `useFilters` hook, so a filtered view is shareable and survives refresh.
- **A selection the server already decides defaults to empty, not to the resolved value.**
  Empty means "wherever the record is now", so a shared link keeps tracking it; only an
  explicit choice writes a value. **And it is dropped when the thing it pins moves** — watch
  the record's status and clear the pin when it changes, rather than teaching each action to
  unpin.
- **A redirect waits for what it decides on.** A flag set or permission list that answers
  "empty" while in flight is indistinguishable from "everything off". Render a spinner until
  it resolves; `replace`-ing a route off an unresolved answer cannot be walked back.
- Guard redirects preserve intent: `/login?next=…`, and return them after.
- **Routes are eager by default.** Split a route when it drags a heavy dependency in behind
  it, not on principle — [performance](../performance.md).
- Moving between steps of a form is `navigate()`, so back/forward walk the wizard. An unknown
  step key redirects to the first valid one; a valid deep link is preserved.

## Filters in the query string

Four rules, enforced by the shared hook:

1. **A value equal to its default is removed, never written.** Otherwise `?q=&page=1` is the
   resting state and every shared link is noise.
2. **A filter change `replace`s.** Only moving between screens pushes.
3. **Any filter change resets `page`.**
4. **A text input is local and debounced into the URL.**

The filter string is also the list query's cache key, so browser-back reads from cache.

## Multiple audiences

If a product ships separate builds per audience (customer, vendor, back office), each is its
own route module selected at build time, served from its own hostname at its own root — no
`/admin` prefix, no cross-links, because they are separate origins and the cookie is
host-only. A shared component that must branch on the site reads a build-time constant; it
cannot import the route module that imports it. A new route belongs to exactly one module.

Genuinely shared public-auth screens (MFA, verify email, reset password) live in one shared
module every site mounts.

## Layouts

Layouts are route elements with `<Outlet />`, not wrappers repeated in every page component.
An admin area is a **sibling** of the customer area, not a child — nesting it would put it
inside guards and shells wired to the customer's own data.

## Navigation config

One flat ordered array of nav items is the single source of truth. A home redirect sends a
principal to the first entry they can see, so declaration order is behaviour. Two lists per
item: what *opens* the page (`requiredPermissions`) and what the rail *advertises*
(`railPermissions`) — a permission the work needs is not a claim on the screen that
configures it. A guarded route redirects to a dedicated "no access" page, never to `/`,
which on an admin site is itself.

**See also:** [state](state.md) · [security](../security.md) · [feature flags](feature-flags.md)
