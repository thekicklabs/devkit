# Pattern — test factories

**Read when:** creating model instances in a test.
**Prereq:** [testing](../testing.md)

**Always use factories. Never hand-construct a model in a test.**

---

## Usage

```python
activity = await ActivityFactory.create_async(session=db_session)  # parents auto-created
activity = await ActivityFactory.create_async(session=db_session, user=test_user)
activity = await ActivityFactory.create_async(session=db_session, type="EVENT", title="My Event")
```

## The base factory

It exists to solve two problems that bite every SQLAlchemy test suite:

1. **Auto-creates required FK parents.** A non-nullable `user_id` gets a real `User` row.
2. **Sets nullable FKs to `None`.** Otherwise polyfactory generates a random UUID for an
   optional FK, which violates the constraint.

```python
class SQLAlchemyBaseFactory(SQLAlchemyFactory[T]):
    __is_base_factory__ = True
    __set_relationships__ = False

    @classmethod
    async def _auto_create_required_parents(cls, session, kwargs):
        rel_map = _get_rel_fk_map(cls.__model__)
        required_rels = _get_required_rels(cls.__model__)
        resolved = dict(kwargs)

        for rel_name, pairs in rel_map.items():
            fk_provided = any(local_attr in resolved for local_attr, _ in pairs)
            if rel_name in resolved or fk_provided:
                continue

            if rel_name in required_rels:
                target_model = mapper.relationships[rel_name].entity.class_
                factory = _get_factory_for_model(target_model)
                parent = await factory.create_async(session=session)
                for local_attr, remote_attr in pairs:
                    resolved[local_attr] = getattr(parent, remote_attr)
            else:
                for local_attr, _ in pairs:
                    col = mapper.columns.get(local_attr)
                    if col is not None and col.nullable:
                        resolved[local_attr] = None

        return resolved

    @classmethod
    async def create_async(cls, session, **kwargs):
        kwargs = cls._resolve_relationship_kwargs(kwargs)
        kwargs = await cls._auto_create_required_parents(session, kwargs)
        obj = cls.build(**kwargs)
        session.add(obj)
        await session.flush()  # get the id, no commit
        return obj
```

`flush()`, never `commit()` — the test's SAVEPOINT owns the transaction. See
[session](session.md).

## The five rules

polyfactory generates plausible-looking randomness for anything a factory does not pin, and
each failure lands a long way from its cause.

1. **Pin every CHECK-constrained column.** A random enum member satisfies the constraint and
   is still the wrong answer for the test; a random combination of booleans violates a
   multi-column check one build in sixteen. Pin the member, not just the column's validity.
2. **Pin every partial-index column.** A `UNIQUE … WHERE is_active` allows one active row,
   so `is_active` defaults to `False` and the test that wants an active row passes it.
3. **Pin every nullable FK *column* that has no relationship.** The base factory nulls
   nullable FKs by walking *relationships*; a column with none is invisible to it and gets a
   random uuid pointing at no row.
4. **No collection relationships anywhere** — see [models](models.md). A NOT NULL FK does
   need its many-to-one, or the factory cannot build the parent.
5. **Every factory module is imported in `conftest.py`.** `_get_factory_for_model` scans
   `SQLAlchemyBaseFactory.__subclasses__()`, which only lists classes that have been imported.

Column types bite too: `Numeric(5, 2)` overflows on a random `Decimal`, `SmallInteger` on a
random `int`, `INET` rejects a random string. Pin those the same way.

**See also:** [testing](../testing.md) · [models](models.md)
