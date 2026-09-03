---
name: typescript
description: strict TypeScript — no any, no barrels, flat files; Vitest + Testing Library basics; lint/typecheck/test/build gate
route: TypeScript code
---
# TypeScript — router

**Read when:** any task touching TypeScript.
**Prereq:** `../workflow.md`

`strict: true` · ESM · a linter (`oxlint` or `eslint`) · Vitest · `npm` scripts as the
interface: `dev` `build` `typecheck` `lint` `format` `test`.

## Routing

| Doing… | Read |
| --- | --- |
| Writing or fixing tests | [`testing.md`](testing.md) |
| A React app | `../react/AGENTS.md` (when installed) |

## Non-negotiables

1. **`strict: true`, no `any`, no unexplained `@ts-expect-error`.** `unknown` at a boundary,
   narrowed; a suppression carries the specific reason on the same line.
2. **No barrels.** An `index.ts` that re-exports gives every symbol two import paths — two
   things to grep for and the shortest road to a circular import. Import the full path.
3. **Flat files until they hurt.** `hooks.ts` becomes `hooks/` when it gets long, not before.
4. **Parse at the boundary.** Anything arriving over the wire is validated (Zod or
   equivalent) once, where it arrives — not trusted three modules deep.
5. **Named exports.** A default export is anonymous at the import site and renames silently.
6. **No `console.log` left behind.** A logger with levels if the project needs one.

## Types

- Derive, don't duplicate: `z.infer<typeof schema>`, `ReturnType<>`, `Parameters<>`, `as const`
  for closed sets. A hand-written twin of a schema is a twin that drifts.
- A union of literals over an `enum` unless the enum is shared with a wire contract.
- `readonly` on anything that must not be mutated in place.

## Before you say done

```bash
npm run lint && npm run typecheck && npm run test && npm run build
```

All four, all clean, output pasted. `build` is part of the gate because `tsc -b` and the
bundler catch what the editor did not.
