# Pattern — services and routes

**Read when:** adding or changing any endpoint.
**Prereq:** [session](session.md) · [errors](errors.md)

There is **no repository layer** and no SQLModel. Deliberately. Services are plain async
functions that take a session and run queries. Don't add an abstraction over that.

This file owns the *shape* of a service. Where its file goes is
[service modules](service-modules.md).

---

## Routes are thin

A route handles parameter extraction, calls a service, and serializes the response. Nothing
else. No branching on business state, no queries, no `session.add()`, no `try`/`except`.

```python
@router.post("/activities", response_model=ActivityRead)
async def create_activity(
    session: SessionDep,
    current_user: CurrentUser,
    activity_in: ActivityCreate,
) -> Any:
    activity = await create_activity_for_user(session, activity_in=activity_in, user=current_user)
    return ActivityRead.model_validate(activity)
```

If a route grows an `if` that isn't about HTTP, that logic belongs in the service. If it
grows an `except`, a domain exception is missing — [errors](errors.md).

## Service signature

**`db_session` is always the first positional parameter. Everything after it is
keyword-only.** This is what makes services callable identically from routes, from ARQ tasks,
and from tests.

```python
async def create_activity_for_user(
    db_session: CustomAsyncSession,
    *,
    activity_in: ActivityCreate,
    user: User,
) -> Activity:
    activity = Activity(**activity_in.model_dump(), user_id=user.id)
    db_session.add(activity)
    await db_session.flush()  # get the id without committing

    add_to_arq_after_commit(db_session, "process_activity_task", activity.id)
    return activity
```

`flush()` — never `commit()`. The request lifecycle owns the transaction.

## Reads

```python
async def get_activity(
    db_session: CustomAsyncSession, *, activity_id: uuid.UUID, user: User
) -> Activity:
    result = await db_session.execute(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == user.id)
    )
    activity = result.scalar_one_or_none()
    if activity is None:
        raise ActivityNotFound(activity_id)
    return activity
```

**Raise, don't return `None`.** The service knows why it cannot proceed; the handler
renders it. A `Model | None` return is for genuinely optional lookups (`get_by_email` used
by registration to check availability), not for "not found" on a resource the caller asked
for by id.

## Lists

Every user-facing list endpoint is cursor-paginated — see [pagination](pagination.md). The
`page`/`per_page` shape is **only** for internal or fixed-size admin queries, and returns
`tuple[list[Model], int]`.

## Endpoints that answer everyone, differently

A route that answers an anonymous caller *and* a signed-in one differently takes an
`OptionalUser` dependency (`User | None`, no 401) that shares its cookie/token resolution
with the required-user dependency, so "is this session good" has one home. The service takes
`user: User | None` and decides. The route still holds no logic, and the response must not be
client-cacheable — [security](../security.md#response-caching).

## Typing

- No `Any` in a service signature unless the value is genuinely any type.
- Return the model, or a tuple — not a dict, unless the shape is genuinely ad hoc
  (aggregates, pagination rows).
- No local imports. If you hit a circular import, the module boundary is wrong.

**See also:** [session](session.md) · [errors](errors.md) · [pagination](pagination.md) ·
[models](models.md)
