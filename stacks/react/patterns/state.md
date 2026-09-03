# Pattern — where state lives

**Read when:** you're about to add a `useState`.

Four homes. Everything belongs to exactly one of them.

| State | Home | Never |
| --- | --- | --- |
| Anything the server owns | **TanStack Query** | Copied into `useState` on load |
| Form field values, validation, dirty/touched | **React Hook Form** | Mirrored into Zustand |
| Which screen / step / filter you're on | **The URL** (React Router) | `useState('home')` |
| Theme, locale, sidebar open, layout preference | **Zustand** | Prop-drilled through the tree |

Genuinely local, genuinely ephemeral UI state — a hover flag, an uncontrolled disclosure —
stays in `useState` in the component. That's the only remaining case.

---

## Server state → TanStack Query

Query data is never copied into local state. `const [app, setApp] = useState(data)` forks the
cache and the two diverge. Derive instead:

```tsx
const { data: application } = useApplication(id)
const missingDocs = application?.documents.filter(d => d.required && !d.uploaded) ?? []
```

Mutations invalidate; they don't `setState` — [data](data.md).

## Form state → React Hook Form

Step values, errors, and dirtiness are RHF's. A store holds only a *preference* about the
form (stepper vs long-form), which survives navigation and isn't form data — [forms](forms.md).

## Navigation state → the URL

Current step, active filter, open tab go in the path or the query string — [routing](routing.md).

## Client state → Zustand

Two stores, and a high bar for a third:

- **`themeStore`** — light/dark/system and locale. Persisted. Applies `data-theme` and
  `lang` **before paint**.
- **`uiStore`** — sidebar open, layout mode, chart/table preference.

```ts
const theme = useThemeStore(s => s.theme)   // narrow selector, always
```

A store is for state that is genuinely global and genuinely client-owned. If only one subtree
needs it, that's props or context. If the server owns it, it's Query.

**See also:** [data](data.md) · [forms](forms.md) · [routing](routing.md) · [performance](../performance.md)
