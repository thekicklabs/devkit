# React — Performance

**Read when:** something feels slow, or the bundle grew.

Profile before changing anything. React DevTools Profiler for renders, the Network panel for
requests, `npm run build` output for bundle size. A `useMemo` added on suspicion usually costs
more than it saves.

---

## Query configuration

```ts
// lib/queryClient.ts
defaultOptions: {
  queries: {
    staleTime: 30_000,          // don't refetch on every mount
    refetchOnWindowFocus: false // forms lose focus constantly
  }
}
```

- **Invalidate the narrowest key.** `invalidateQueries()` with no argument refetches
  everything; during autosave that's a request per pause — [data](patterns/data.md).
- Autosave is debounced and flushed on focus-out — [forms](patterns/forms.md).
- Separate resources are separate queries: uploading one document invalidates the documents
  key, not the whole parent.

## Rendering

- **Select narrowly from Zustand.** `useThemeStore(s => s.theme)`, never `useThemeStore()`.
- RHF is uncontrolled by design. Don't `watch()` the whole form to display one value; use
  `useWatch` on that field.
- Don't virtualise speculatively. `React.memo` only after the Profiler shows the re-render.

## Bundle

- **Split a route when it drags a dependency in behind it** (a charting library, an editor),
  not on principle — a split per screen buys request latency, not bundle size. Lazy with a
  skeleton fallback — [routing](patterns/routing.md).
- Import icons individually: `import { Upload } from 'lucide-react'`. Never `import * as`.
- Check `npm run build` output after adding a dependency.

## Fonts and assets

- Self-hosted `.woff2`, `font-display: swap`, preloaded. No CDN font requests.
- Explicit `width`/`height` on images so layout doesn't shift.

## Theme

`data-theme` is applied **before paint** from the theme store, or the page flashes. That's the
one piece of blocking work worth having.

**See also:** [data](patterns/data.md) · [state](patterns/state.md) · [debug](debug.md)
