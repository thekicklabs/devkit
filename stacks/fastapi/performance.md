# FastAPI — Performance

**Read when:** an endpoint is slow, or you're adding one that fans out over rows.

Measure before you change anything. `EXPLAIN ANALYZE` the actual query with production-shaped
row counts — an optimisation guessed from reading code is usually the wrong one.

---

## N+1 queries

The default failure. A list endpoint loads 25 rows, then lazily loads a relationship per row.

```python
query = select(Application).options(selectinload(Application.owner))
```

- `selectinload` for collections (one extra `IN` query).
- `joinedload` for many-to-one scalars.
- Never rely on lazy loading in a list path. With async SQLAlchemy it doesn't silently
  degrade — it raises `MissingGreenlet`.

## Indexes

Add the index **with** the query that needs it, in the same change, via a migration.

- Index the columns you filter and sort on — including the cursor's sort keys.
- Composite index column order must match the query's leading predicates.
- An index on a large table is created concurrently — [migrations](patterns/migrations.md).
- Don't add speculative indexes. Each one costs every write.

## List endpoints

- Cursor pagination, always — [pagination](patterns/pagination.md). Offset gets linearly
  slower with depth.
- **The count query is often the expensive half.** If the UI doesn't need an exact total,
  don't compute one.
- `limit` is clamped in the route.

## Push work off the request

If it's slow and the response doesn't depend on it, it's a task — [tasks](patterns/tasks.md).
A report the client waits for is still a task: it returns a job row the browser polls.

## Cache what many requests ask identically

An expensive aggregate every operator hits with the same filters is a cache —
[caching](patterns/caching.md). It does not replace an index; measure first.

## Connection pool

`pool_size=10` per process. Sizing is `workers × pool_size ≤ Postgres max_connections`, with
headroom for migrations and the workers. Raising `pool_size` to fix slowness usually just
moves the queue.

## Payloads

- Return only the columns the client uses. A `*Read` schema that mirrors every column ships
  data nobody renders.
- Don't return nested collections unbounded. If a parent can have 200 children, the children
  are their own paginated endpoint.

**See also:** [pagination](patterns/pagination.md) · [caching](patterns/caching.md) ·
[debug](debug.md)
