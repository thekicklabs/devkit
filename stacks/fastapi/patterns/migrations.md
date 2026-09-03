# Pattern — Alembic migrations

**Read when:** you touched anything under `app/models/`.
**Prereq:** [models](models.md)

---

## The rule

**A SQLAlchemy column change is not done without a matching Alembic migration in the same
change.** New column, length change, type change, nullable change, default change, index —
all of it.

Models do not auto-sync, and nothing in CI diffs them against the database. Drift fails
silently in production, long after the commit that caused it.

```bash
uv run alembic revision --autogenerate -m "add applications.status"
# Read the generated file. Autogenerate misses: server defaults, index renames,
# enum-width changes, CHECK constraints, and anything behind a property.
uv run alembic upgrade head
uv run alembic downgrade -1     # prove the downgrade before committing
uv run alembic check            # fails if models and migrations have drifted
```

Then run the suite. A migration that isn't applied in tests isn't verified.

New model modules must be imported in `alembic/env.py`, or autogenerate reads their absence
as "drop that table".

## Widen before you lengthen

**Before adding a longer enum or status value, widen the column's real `VARCHAR(n)` to fit
it.** Check the actual `create_table` / most recent `alter_column` in the migration history —
**not** a docstring, and not the model's `String(length=...)`, which may already have drifted
ahead of the database.

```bash
grep -rn "your_column" alembic/versions/ | tail -20
```

The failure mode is a `StringDataRightTruncation` at write time on production data only,
because staging had shorter values.

## Writing the migration

- Sequential revision identifiers and filenames: `v1`, `v2`, …, `vN` — `revision = "v7"`,
  `down_revision = "v6"`, filename `v7_<slug>.py`. Do not keep Alembic's hash or timestamp.
- One migration per logical change. Don't batch unrelated schema edits.
- Provide a real `downgrade()`. If the change is genuinely irreversible, say so in the
  docstring rather than leaving a stub `pass`.
- Data migrations go in the same file as the schema change they depend on, after it — read
  [data migrations](data-migrations.md) first.
- Adding a non-nullable column to a populated table is three steps: add nullable → backfill →
  set not-null. Not one.
- Index creation on a large table is `postgresql_concurrently=True` inside
  `op.get_context().autocommit_block()`.

**See also:** [models](models.md) · [data migrations](data-migrations.md) ·
[review](../review.md)
