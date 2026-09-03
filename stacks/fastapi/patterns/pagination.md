# Pattern — cursor pagination

**Read when:** adding or changing any list endpoint.

**Every user-facing list endpoint paginates with an opaque cursor. Never offset-paginate.**

---

## Response shape

```json
{ "items": [...], "next_cursor": "…" }
```

`next_cursor` is `null` on the last page. Aggregates (e.g. `counts`) go as siblings of
`items`. Recompute them per page — the query is cheap — or document explicitly if you only
return them on the first page.

Define a `*ListPage` Pydantic schema. **The route returns that, not `list[Item]`.**

```python
class ApplicationListPage(BaseModel):
    items: list[ApplicationRead]
    next_cursor: str | None
```

## Service signature

```python
async def list_applications(
    db_session: CustomAsyncSession,
    *,
    limit: int = 25,
    cursor: str | None = None,
) -> tuple[list[Application], str | None]:
```

Always return a tuple — including the empty path (`return [], None`).

## Encoding

`app.core.pagination.encode_cursor(key, row_id)`. `key` is a `date`/`datetime`, or a
`;`-joined composite string. `decode_cursor` splits on the **first `|`** — so `;` separates
components *inside* the key, and `|` separates key from id. Never put a `|` in a key
component. Cursors are opaque to the client and must not encode anything the caller should
not see.

## Query

1. Order by `(sort_keys…, id DESC)`. `id` is the stable tiebreaker — without it, rows with
   equal sort keys can repeat or vanish across pages.
2. Fetch `limit + 1` rows.
3. If the extra row came back, drop it and encode `next_cursor` from the **last kept** row.
4. **The `WHERE` clause must mirror the `ORDER BY`.** For mixed asc/desc compound sorts,
   expand the strict-after comparison with `or_`/`and_` — do not rely on ROW comparisons.

```python
query = select(Application).order_by(Application.created_at.desc(), Application.id.desc())

if cursor:
    created_at, row_id = decode_cursor(cursor)
    query = query.where(
        or_(
            Application.created_at < created_at,
            and_(Application.created_at == created_at, Application.id < row_id),
        )
    )

rows = (await db_session.execute(query.limit(limit + 1))).scalars().all()
has_more = len(rows) > limit
rows = rows[:limit]
next_cursor = encode_cursor(rows[-1].created_at, rows[-1].id) if has_more and rows else None
return list(rows), next_cursor
```

## Route

Clamp the limit: `limit = max(1, min(limit, 100))`. An unclamped limit is a
denial-of-service parameter.

Search / `q` modes may return a single ranked page with `next_cursor=None` — document that in
the endpoint docstring so callers don't treat it as end-of-list for the unfiltered query.

## Tests

Cover: first page · following a cursor to page 2 · the last page returning `next_cursor=None` ·
no duplicate or skipped ids across pages when sort keys tie.

**See also:** [services & routes](services-routes.md) · [performance](../performance.md)
