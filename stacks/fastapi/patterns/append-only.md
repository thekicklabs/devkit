# Pattern — append-only tables

**Read when:** adding a table that records evidence (submissions, status history, audit
events), or touching one.
**Prereq:** [models](models.md)

Some tables are evidence: what someone submitted, and when a record changed hands. An
`UPDATE` against one of those is never a legitimate operation, so the **database** refuses
it rather than trusting every future caller to remember.

The second reason to reach for this: a property that must hold ("converting a note never
changes the original's visibility") is something to prove by test if the row is mutable,
and true by construction if it is not. Keep the parent mutable with a projected `state`
column; the event table is the record behind it.

---

## Declaring one

```python
from app.models.append_only import make_append_only


class ApplicationSubmission(Base): ...


make_append_only(ApplicationSubmission)
```

`make_append_only` attaches `deny_mutation()` triggers — one `FOR EACH ROW` covering UPDATE
and DELETE, one `FOR STATEMENT` covering TRUNCATE — to the table's **`after_create`** event.

## Why `after_create` and not only the migration

`tests/conftest.py` builds the schema with `Base.metadata.create_all` and never runs Alembic.
A trigger that lived only in a migration would be completely untested. Attaching it to
`after_create` means `create_all` emits it too, and a test exercises the real thing.

**The migration still carries its own copy of the SQL, verbatim.** A migration is a
historical snapshot: it has to keep applying to a fresh database years after this module
has been refactored. Importing from `app/models/` couples the past to the present.

## What this forbids in a service

1. **No `TimestampMixin`.** An append-only row has no `updated_at` to maintain.
2. **Never mutate a loaded instance.** `expire_on_commit=False` keeps instances in the
   identity map for the whole request, so touching any attribute emits an UPDATE at the next
   flush and the trigger rejects it. Read one, or insert one. Not both.
3. **No relationship pointing at one may carry a delete cascade**, and the parent declares
   no reverse collection — a cascade would try to DELETE and the trigger would refuse,
   failing the unrelated request that deleted the parent.

## The other layers

The trigger is one of three, because any one alone is bypassable: the application role
should hold `INSERT, SELECT` only, and migrations should run as a separate schema-owning
role. Until both are configured, a table owner can disable its own triggers — so the trigger
is a guard, not a guarantee. Know which you have.

Erasure requests are the one legitimate reason to remove rows, and they are a documented
procedure run outside the application — not a delete path left open in a service. A guarded
rewrite is the other sanctioned exception — [data migrations](data-migrations.md).

**See also:** [models](models.md) · [migrations](migrations.md) ·
[data migrations](data-migrations.md) · [session](session.md)
