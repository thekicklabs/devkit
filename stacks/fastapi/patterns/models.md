# Pattern — models

**Read when:** adding or changing a SQLAlchemy model.
**Always paired with:** [migrations](migrations.md) — in the same commit.

---

## Base and mixins

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Base(AsyncAttrs, DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
```

- UUID primary keys by default.
- `datetime.now(timezone.utc)` — **never** `datetime.utcnow()`.
- Table names auto-derive from the class name. Override only when the plural is wrong or a
  prefix is the namespace.

## Every model keeps `Base`'s `id`

Adding `primary_key=True` to another column does **not** replace it. It *appends*, giving a
composite `PRIMARY KEY (id, other_column)` plus a uuid nobody uses — with no error and no
autogenerate diff. A model-invariants test fails the build on it.

A 1:1 satellite table expresses its identity as a **UNIQUE NOT NULL foreign key** instead:

```python
class ProfileDetails(Base):
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
```

Same guarantee, one primary key.

## Relationships: many-to-one only

**No model declares a collection relationship.** The test factory treats a relationship as
required when its local column is NOT NULL — and for a one-to-many that column is the
*parent's own primary key*. A collection therefore makes the parent build a child, which
builds a parent, until the stack runs out.

Children declare the many-to-one; parents declare nothing. Query the child by its foreign key.

The many-to-one is not optional either: it is how the factory resolves a required FK parent.
A NOT NULL foreign key with no relationship beside it gets a random uuid and a constraint
violation — see [factories](factories.md).

## Enums are strings in the database

Store the value in a `VARCHAR` column. Do not use PostgreSQL enum types. Map it with
SQLAlchemy's `Enum(native_enum=False)` — the type handles the conversion and emits the
`CHECK` for you.

```python
from sqlalchemy import Enum as SAEnum  # `Enum` is taken by the stdlib import


class ActivityType(str, Enum):
    MOVIE = "movie"
    EVENT = "event"


class Activity(TimestampMixin, Base):
    type: Mapped[ActivityType] = mapped_column(
        SAEnum(
            ActivityType,
            native_enum=False,
            length=10,
            create_constraint=True,
            name="ck_activities_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        index=True,
    )
```

That emits `VARCHAR(10)` plus `CHECK (type IN ('movie', 'event'))`. Reads give you a real
enum member, so compare with `is ActivityType.MOVIE` rather than against a string.

**`values_callable` is not optional.** SQLAlchemy persists member *names* by default, so
without it a `HISTORY_ONLY = "history_only"` member is stored as `'HISTORY_ONLY'`.

**`create_constraint` is not optional either.** It defaults to `False`, so `native_enum=False`
alone gives a bare `VARCHAR` with nothing validating it.

**Why not PG enums:** adding or removing a value needs `ALTER TYPE` plus migration
coordination. A `VARCHAR` migrates trivially, and indexing behaves identically.

> Before adding a longer enum value, widen the column's real `VARCHAR(n)` first — see
> [migrations](migrations.md).

**`alembic check` does not compare CHECK constraints**, and a test schema built with
`create_all` emits the constraint from the model — so the suite passes green against a
database that never got it. When adding a constraint to an existing column, confirm against
the real database:

```bash
psql -c "SELECT conname FROM pg_constraint WHERE conrelid = 'your_table'::regclass AND contype = 'c'"
```

## Boolean predicates — `.is_()`, not `==`

```python
.where(Reminder.is_accepted == False)      # trips E712, reads as Python truthiness
.where(Reminder.is_accepted.is_(False))    # explicit SQL IS FALSE
```

Same rule for `.is_(None)` over `== None`.

**See also:** [migrations](migrations.md) · [services & routes](services-routes.md)
