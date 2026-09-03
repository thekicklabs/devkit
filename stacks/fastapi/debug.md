# FastAPI — Debug

**Read when:** chasing a backend bug. The `debug` skill is the method; this is the table.

---

## Symptom → cause

| Symptom | Look at |
| --- | --- |
| **Hook didn't fire / job never enqueued** | The transaction didn't commit. Something raised after the service ran, or the test used `TestAsyncSession` (which captures without firing). |
| **Row missing right after creating it** | A service called `flush()` but the request errored before commit — everything rolled back. Check the response status, not the log line. |
| **Row invisible to a `select()` in the same request** | `autoflush=False` and no `flush()` — [session](patterns/session.md). |
| **`MissingGreenlet` / lazy-load error** | Relationship accessed outside the loaded scope. Add `selectinload` — [performance](performance.md). |
| **Column doesn't exist / wrong values after deploy** | Missing migration, or stale prepared statements. See below. |
| **Task retries forever** | The exception isn't in `ignore_exceptions`. Raise `JobExecutionFailed` for permanent failures — [tasks](patterns/tasks.md). |
| **Task never runs** | Not registered in the worker's function list. Enqueue succeeds regardless. |
| **Job polled forever** | The task raised on its last try, so the failure status rolled back — [tasks](patterns/tasks.md). |
| **`StringDataRightTruncation`** | A value outgrew its real `VARCHAR(n)` — [migrations](patterns/migrations.md); check the migration history, not the model. |
| **Duplicate/missing rows across pages** | `ORDER BY` missing the `id` tiebreaker, or `WHERE` not mirroring it — [pagination](patterns/pagination.md). |
| **500 where a 4xx was expected** | The service raised a bare exception instead of an `AppError` — [errors](patterns/errors.md). |
| **Test passes alone, fails in the suite** | Shared state that isn't rolled back, or a mock patched inline instead of as an `autouse` fixture. |
| **Comma-separated setting raises at startup** | `list` setting without `NoDecode` — `../python/AGENTS.md`. |

## Stale prepared statements

Symptoms: correct-looking queries returning values from the wrong columns, immediately after a
migration, on some connections but not others.

Cause: pooled connections reused cached prepared statements pointing at old column positions.
Fix and prevention: `connect_args={"prepared_statement_cache_size": 0}` —
[session](patterns/session.md). Verify that setting first before reading anything else.

## Reading the rollback path

`session.commit()` has three failure regions, and they behave differently:

1. **Before-commit hooks fail** → rollback, request errors. Nothing persisted, nothing queued.
2. **`COMMIT` itself fails** → rollback, request errors.
3. **After-commit hooks fail** → **data is already committed.** The error is logged and the
   request still errors, but the write stands. A retry may double-apply.

When a bug involves partial state, work out which region you're in before touching anything.

## Tools

```bash
uv run pytest path/to/test.py::test_name -x -vv
uv run pytest --lf
```

Set `echo=True` on the engine locally to see emitted SQL. Never commit it. For a slow query,
`EXPLAIN ANALYZE` it directly against the database rather than inferring from ORM code.

**See also:** [testing](testing.md) · [performance](performance.md)
