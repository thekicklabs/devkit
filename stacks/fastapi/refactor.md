# FastAPI — Refactor

**Read when:** restructuring existing backend code. The `refactor` skill is the discipline;
these are the boundaries.

---

## Architectural boundaries — do not "improve" these

Deliberate choices, not gaps waiting to be filled:

- **No repository layer.** Services query the session directly.
- **No SQLModel.** Raw SQLAlchemy models plus separate Pydantic schemas.
- **Services are functions, not classes.** No `ActivityService` with `self`. The one
  exception is an email message object — [emails](patterns/emails.md) has its boundary.
- **Hooks over inline side effects.** Don't "simplify" an `add_to_arq_after_commit` into a
  direct call — [session](patterns/session.md) explains the ordering.
- **Services raise; routes don't map.** Don't reintroduce `Model | None` returns with the
  route deciding — [errors](patterns/errors.md).

If one of these genuinely blocks you, raise it. Don't route around it in a diff.

## Safe moves

- Splitting a long service module by domain — free, imports only.
- Extracting a shared query helper — free, as long as it still takes `db_session` first.
- Renaming a Python symbol — free.
- Tightening types, removing `Any`, removing local imports — always welcome.

## Moves that need a migration

Anything that touches the database is not a refactor, it is a schema change: renaming a
column or table, moving a column, changing type/length/nullability/default, adding or
dropping an index. All of it goes through [migrations](patterns/migrations.md), in the same
commit.

**See also:** [review](review.md) · [performance](performance.md)
