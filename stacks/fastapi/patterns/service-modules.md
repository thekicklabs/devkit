# Pattern — service modules

**Read when:** adding a service, a route, or a task — i.e. almost every backend change.
**Prereq:** [services & routes](services-routes.md)

`services/` holds the business logic. `api/` and `tasks/` are gateways into it and hold none.
That split is the reason a rule change lands in one file instead of two.

---

## One operation, one file

```
app/services/<feature>/<action>.py
```

`<feature>` is the entity or capability — `auth`, `application`, `documents`, `email`.
`<action>` is the operation — `register`, `authenticate`, `submit`, `update_profile`.

```
app/services/
  auth/
    register.py           register_user()
    authenticate.py       authenticate_user()
  user/
    update_profile.py     update_profile()
  email/
    send_welcome.py       send_welcome_email()
```

- **One public async function per module**, named for the file's action. A module with two
  public functions is two modules. The one exception is an email class beside its send
  function — [emails](emails.md) has the rule and its boundary.
- Private helpers live beside it, `_`-prefixed. Once a second feature needs one, it moves to
  `core/` — copying it is how two behaviours start drifting apart.
- Exceptions the caller must distinguish are declared next to the function that raises them,
  as `AppError` subclasses — [errors](errors.md).

**`__init__.py` stays empty.** No re-export layer. Import the full path:

```python
from app.services.auth.register import register_user  # the only way in
```

A re-export gives every function two import paths, and two paths are two things to grep for.
It is also the shortest road to a circular import once features start calling each other.

## Gateways hold no logic

A route extracts parameters, calls a service, serializes, returns. A task unwraps `ctx`, calls
a service, and translates the result into retry-or-fail.

```python
@arq_retry()
@arq_inject_db_session
async def send_welcome_email_task(ctx: dict[str, Any], user_id: uuid.UUID) -> None:
    db_session = ctx["db_session"]

    delivered = await send_welcome_email(db_session, user_id=user_id)
    if not delivered:
        raise JobExecutionFailed(f"User not found: {user_id}")
```

The `if` above is about job retry semantics, not about domain policy — that is the line. An
`if` in a route that isn't about HTTP, or in a task that isn't about retrying, belongs in a
service.

**Services never import from `api/` or `tasks/`.** The dependency runs one way. A service that
needs a `Request` or a `ctx` is a service that was handed the wrong argument.

## Where things that aren't operations go

| It is… | It lives in |
| --- | --- |
| Business logic for one operation | `services/<feature>/<action>.py` |
| A helper two features both need | `core/` |
| A constant driving one operation | Module-level in that service file |
| A SQLAlchemy model | `models/` — never a query helper on the model |
| Request/response shape | `schemas/` |
| Auth, hashing, cursors, session hooks, errors | `core/` |

`core/` is infrastructure — it must not import from `services/`, `api/`, or `tasks/`.

**See also:** [services & routes](services-routes.md) · [tasks](tasks.md) ·
[session](session.md) · [feature](../feature.md)
