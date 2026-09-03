# Pattern — data layer

**Read when:** fetching anything, or adding a mock endpoint.

**MSW is the default dev data source; the API is the authority.** No component holds
hardcoded domain data — it lives in `src/mocks/seed.ts`.

---

## Layers

```
src/lib/api.ts            fetch wrapper — base URL, credentials, error normalisation
src/lib/queryClient.ts    QueryClient defaults + query key factories
src/features/<f>/api.ts   typed request functions for that feature
src/features/<f>/hooks.ts useX() query + mutation hooks
src/features/<f>/wire.ts  Zod for the response shapes
src/mocks/handlers.ts     MSW handlers
src/mocks/seed.ts         seed data + resetDb()
src/mocks/browser.ts      dev worker      src/mocks/server.ts   node server for tests
src/types/index.ts        entities shared across features
```

Components call hooks. Hooks call `api.ts`. Only `api.ts` knows about `fetch`.

`seed.ts` exports **`resetDb()`**, called in `afterEach` — mocked writes are stateful within
a test and reset between them. If the seed writes through a Proxy that traps only top-level
`set`, reassign (`db.list = [...]`) rather than mutating in place.

## Errors

`lib/api.ts` throws an `ApiError` carrying `status` and the parsed envelope
`{ error: { code, message, details } }`. **Everything downstream switches on `error.code`,
never on status** — status is transport. Render the message with `t(\`errors.${code}\`)`
([i18n](i18n.md)); branch on the code where behaviour differs (a 409 that means "already
submitted" navigates; one that means "version conflict" refetches).

A bare `fetch` throws a plain `Error` with no status and no code. Never use one.

## Query keys

Hierarchical, exported so invalidation is greppable:

```ts
export const applicationKeys = {
  all: ['applications'] as const,
  lists: () => [...applicationKeys.all, 'list'] as const,
  detail: (id: string) => [...applicationKeys.all, id] as const,
  documents: (id: string) => [...applicationKeys.detail(id), 'documents'] as const,
}
```

Flat singletons (`['application']`) are wrong once resources are id-addressed: invalidating
one record's children has to reach that record's and nobody else's.

Invalidate the narrowest key that covers the change. `queryClient.invalidateQueries()` with
no argument refetches the entire app.

## Mutations

```ts
const { mutate, isPending } = useMutation({
  mutationFn: submitApplication,
  onSuccess: () => queryClient.invalidateQueries({ queryKey: applicationKeys.detail(id) }),
})
```

Mutations invalidate. They never write to local state — [state](state.md).

`setQueryData` is for a response that *is* the new state of a resource the client already
holds — a draft returned by an autosave, whose `lockVersion` the next save must echo.
Invalidate whenever the server reconciles something only it knows the result of.

## Polling a job

Server work the browser waits on is a queued job, not a slow response:

```ts
refetchInterval: (query) => {
  const status = query.state.data?.status
  return status === 'ready' || status === 'failed' ? false : POLL_INTERVAL_MS
}
```

1. **The interval returns `false` on a terminal status.**
2. **Polling gives up after a maximum** and offers a button instead. The job keeps running
   server-side; only the asking stops.
3. **Changing the inputs discards the job.** A result answers the inputs it was requested
   with.

The run state lives *above* the control that starts it — a popover panel that unmounts on
close would take a running job with it. One `useMutation` cannot report per-item progress
(`isPending` is shared); the phase comes from the run.

This is the only place that overrides the global `staleTime` / `refetchOnWindowFocus`.

## Boundary validation

Parse responses with the feature's `wire.ts` schema at the `api.ts` boundary. A shape change
from the backend fails loudly there, once — not as `undefined` three components deep. The
one deliberate exception is a draft payload, which is whatever the user has typed so far.

Multipart goes through the same wrapper — it drops the JSON content type so the boundary
survives.

## Runtime knobs

Anything the API is the authority on — environment, TTLs the copy quotes, feature flags —
comes from `GET /config` via `useAppConfig()`, never from a constant in the SPA. That hook
does not retry and has no error state, so **every consumer degrades to saying nothing**:
render the sentence without the duration rather than "expires undefined".

## Adding an endpoint

1. Wire type in `src/types/index.ts`, matched to the backend's response schema.
2. MSW handler + seed data, written **against the backend's real contract** — list shapes
   are `{ items, nextCursor }`, and a 404 the client reads as "not started yet" has to be a
   404 in the mock too.
3. Request function in `features/<f>/api.ts`, response parsed with `wire.ts`.
4. Hook in `features/<f>/hooks.ts`.
5. Test — the MSW node server serves the same handlers.

## Loading, error, empty

Every query-backed view renders all three. `Skeleton`/`Spinner` for loading, `Alert` for
error with a retry, a real empty state — not a blank div.

**See also:** [state](state.md) · [i18n](i18n.md) · [performance](../performance.md)
