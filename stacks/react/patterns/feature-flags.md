# Pattern — feature flags

**Read when:** hiding a surface that is built but not ready to be used.

---

## What a flag is

A row the API serves (`GET /feature-flags`), not an env var and not a build-time constant.
A global row plus optional per-user overrides in **both** directions. No write endpoint and
no admin screen, deliberately: a flag is short-lived, and a UI for managing them makes them
furniture.

**A flag is temporary.** When the feature becomes unconditional, delete the member, every
call site and the rows — together, in one commit.

## Reading one

```tsx
const reviewEnabled = useFeatureFlag(FEATURE_FLAG.ENABLE_REVIEW)
```

- **A failed fetch means everything off.** `retry: false`; the hook degrades to an empty set.
  A flag guards a surface that is not ready, so silence is the safe answer.
- **A flag this build has never heard of is ignored.** The wire schema is
  `z.array(z.string())` so a newer API cannot fail the parse.
- **Signing in re-fetches.** The anonymous answer is already cached by then.

## A flag is not a guard

The API is the authority. Hiding a nav item does not stop the endpoint answering, and is not
meant to — a flag says "not ready to show", not "not allowed to see". Where a flagged screen
has its own route, wrap it in `FeatureFlagRoute` so it is not reachable by typing the URL —
the first thing someone does when a link disappears.

**Watch what a flag does to the nav.** If entry to an area is "has at least one visible
item", flagging away every item a role holds locks that role out. Take that decision
deliberately.

**See also:** [routing](routing.md) · [data](data.md)
