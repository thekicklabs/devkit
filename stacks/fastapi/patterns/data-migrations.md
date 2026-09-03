# Pattern — data migrations and guarded rewrites

**Read when:** changing persisted values, especially JSON, arrays, digests, or evidence tables.
**Prereqs:** [migrations](migrations.md) · [append-only](append-only.md)

Confirm before writing one — the workflow's ask/decide table names migration code as an
"ask", because it is often written for a feature nothing uses.

## Alembic or an out-of-band script

Use Alembic when the rewrite is deterministic, small, and must run in every environment. Put
it after the schema operation it depends on in the same revision.

Use `scripts/<YYYYMMDDTHHMM>_<name>.py` when the operation is environment-specific,
long-running, requires a human to inspect its output, or touches data a normal migration must
not rewrite. Such scripts:

- dry-run by default and require an explicit `--apply`;
- report affected row counts before and after;
- are idempotent, so an interrupted run can be repeated;
- refuse production unless explicitly told to run there.

## Guarded append-only rewrite

Changing evidence is exceptional and never becomes an application service path. The
out-of-band procedure:

1. obtain approval and run as the schema owner;
2. record pre-change row counts and verification hashes;
3. `ALTER TABLE ... DISABLE TRIGGER` only for the named table;
4. perform the narrow, idempotent rewrite;
5. recompute every stored digest with the same canonical serialisation that originally
   wrote it — a merely equivalent-looking JSON dump produces a different hash;
6. re-enable the trigger immediately;
7. verify counts, digests, and trigger presence before ending the window.

## Stable identifiers

A key embedded in JSONB, an array column, or an append-only row cannot be safely renamed by
an ordinary deployment. Use semantic identifiers at schema design time; derive display order
from a registry instead of persisting position as identity.

**See also:** [migrations](migrations.md) · [append-only](append-only.md)
