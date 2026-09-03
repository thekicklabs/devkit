# Pattern — Redis response caching

**Read when:** an endpoint recomputes an expensive answer that many requests share.
**Prereq:** [session](session.md) · [performance](../performance.md)

`app/core/cache.py` is the whole of it. It reuses the ARQ pool (`get_arq_redis`) rather than
opening a second connection — one Redis, one pool per process.

---

## When to cache

Only when **all** of these hold:

- The answer is expensive — a fan-out, a repeated scan, an aggregate over the whole table.
- Many requests ask the identical question. A cache keyed on something unique per request is
  a write-only store.
- Reading it a minute stale is *correct behaviour*, not a compromise you are hoping nobody
  notices. Say so in the response: carry a `generatedAt`.

**Not** a substitute for an index. Measure first — [performance](../performance.md).

## The rules

1. **Hash the key. Never embed the inputs.** Filters carry free-text search; Redis keys turn
   up in `MONITOR`, in a slow-log, on a screen behind someone.

   ```python
   key = cache_key(name="dashboard", payload=json.dumps(payload, sort_keys=True))
   ```

   `sort_keys=True` is load-bearing — two dicts that differ only in insertion order are the
   same question and must be the same key.

2. **Put the principal's authorisation in the payload.** Scope and disclosure level go into
   the key even when today's query ignores them. They cost nothing, and they are what stops
   the first scoped version of the endpoint serving one principal's rows to another.

3. **A cache failure is a miss, never a 500.** Every function in `core/cache.py` swallows and
   logs. An endpoint must return the same answer with Redis unplugged, only slower.

4. **Cache the serialized wire shape**, not an ORM object — round-tripping the response
   schema is the version that cannot drift from what the endpoint returns.

5. **TTL is a module constant in the service that owns it**, not a setting. It is a property
   of that query, not of the deployment.

6. **A server-side cache never becomes a client-side one.** Principal-specific responses stay
   `Cache-Control: no-store` — [security](../security.md#response-caching).

## Where it lives

The query stays a pure query; the cache goes in a service beside it that owns the read:

```
services/reporting/get_dashboard.py    the queries, no cache
services/reporting/read_dashboard.py   cache → build → store, returns the response schema
```

The route calls the reader. Putting the cache inside the query would leave no way to ask for
the live answer, which an export needs.

## Invalidation

There is none, deliberately. Entries expire; nothing deletes them. A write path that has to
reach into the cache is a sign the TTL is too long for the data — shorten it rather than
building a second correctness mechanism that can be forgotten on the third call site.

**See also:** [performance](../performance.md) · [tasks](tasks.md) · [session](session.md)
