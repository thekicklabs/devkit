# React — Refactor

**Read when:** restructuring existing frontend code. The `refactor` skill is the discipline;
these are the boundaries.

---

## When to extract

- **To `src/components/ui/`: on the second use, not the first.** One caller is not a
  pattern, and a primitive designed from a single example ends up with the wrong props.
- **To `src/components/` (shared domain widgets): when two features need it.**
- **Duplicate until three.** Two similar-looking blocks that are about to diverge cost far
  less than an abstraction with four boolean props.

## Variants belong in CVA

```tsx
<Button className={isDark ? 'bg-secondary text-white' : 'bg-primary'} />   // leaks to every call site
<Button variant={isDark ? 'dark' : 'primary'} />                            // lives in the component
```

If a call site is composing Tailwind classes to change *appearance*, that's a missing
variant. Layout adjustments (`className="w-full mt-4"`) at the call site are fine — `cn()`
merges them.

## Safe moves

Renaming · splitting a long component file · moving a feature-local component into
`components/` once a second feature needs it · extracting a hook · replacing prop-drilling
with a narrow store selector · tightening types.

## Moves that aren't refactors

- Changing a query key — that changes caching and invalidation. Verify the flows.
- Changing a route path — deep links break; add a redirect.
- Moving state between the four homes in [state](patterns/state.md) — refresh, back-button
  and sharing all change.
- Touching a theme token — every screen is affected. Check both themes.
- Renaming a translation key — every locale file changes with it.

**See also:** [design system](patterns/design-system.md) · [review](review.md)
