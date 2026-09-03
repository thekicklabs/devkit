# React — Debug

**Read when:** chasing a frontend bug. The `debug` skill is the method; this is the table.

Reproduce it in `npm run dev` first, then write the failing test, then fix.

---

## Symptom → cause

| Symptom | Look at |
| --- | --- |
| **Data is empty / `undefined`** | MSW handler path or method doesn't match. Check the Network tab. In tests `onUnhandledRequest: 'error'` fails the test outright. |
| **Query never resolves in a test** | Retries left on. Render through `src/test/render.tsx` with `retry: false`. |
| **Test passes alone, fails in the suite** | Leaked state. `setup.ts` resets handlers, `resetDb()` and `localStorage` — new mutable module state needs adding there. |
| **Stale data after a mutation** | Wrong invalidation key, or data copied into `useState` — [state](patterns/state.md). |
| **Refetch storm during autosave** | `invalidateQueries()` called too broadly — [performance](performance.md). |
| **Page flashes light then dark** | `data-theme` applied after paint — [design system](patterns/design-system.md). |
| **Component invisible in dark mode** | A raw hex instead of a semantic slot, or a light-only tint on a dark surface. |
| **Form won't advance, no visible error** | Zod error on a field that isn't rendered, or a `FormField` missing its `error` prop — [forms](patterns/forms.md). |
| **Submit disabled, no reason shown** | A mirrored gate counting from an unloaded set — it reads as incomplete by design; check the blocker renders. |
| **Second press needed on Save & continue** | The button disabled during the focus-out save that its own mousedown triggered — [forms](patterns/forms.md). |
| **Refresh loses state / back does nothing** | State that belongs in the URL — [routing](patterns/routing.md). |
| **Redirect lands somewhere wrong on load** | A redirect decided on an unresolved query (empty flag set, empty permission list) — [routing](patterns/routing.md). |
| **Styles don't apply / wrong class wins** | Missing `cn()` merge, so Tailwind classes collide instead of overriding. |
| **A key like `errors.NOT_FOUND` on screen** | Missing translation — [i18n](patterns/i18n.md). |
| **Rows re-key onto the wrong inputs** | Row ids minted by hand instead of `useFieldArray` — [forms](patterns/forms.md). |

## Tools

- **React Query Devtools** — every query's key, state, and last fetch. Most "stale data"
  bugs are visible here in seconds.
- **Network tab** — MSW requests show as normal HTTP; unhandled ones warn in the console.
- **React DevTools Profiler** — before any memoisation.
- Toggle the theme on the broken screen. Half of visual bugs only exist in one theme.

```bash
npm run test -- path/to/file.test.tsx -t "test name"
npm run test:e2e -- --headed --debug
```

**See also:** [testing](testing.md) · [performance](performance.md)
