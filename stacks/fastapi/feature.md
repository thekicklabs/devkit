# FastAPI — Feature

**Read when:** adding an endpoint, model, service, or background task.
**Prereqs:** [session](patterns/session.md) · [services & routes](patterns/services-routes.md) · [errors](patterns/errors.md)

---

## Order of work

Follow it top to bottom. Each step names the pattern file that governs it.

| # | Step | Read |
| --- | --- | --- |
| 1 | Model in `app/models/` | [models](patterns/models.md) |
| 2 | **Alembic migration — same commit** | [migrations](patterns/migrations.md) |
| 3 | Pydantic schemas in `app/schemas/` | below |
| 4 | Error codes the operation can raise, in `core/error_codes.py` | [errors](patterns/errors.md) |
| 5 | Service in `app/services/<feature>/<action>.py` | [service modules](patterns/service-modules.md) |
| 6 | Route in `app/api/routes/` | [services & routes](patterns/services-routes.md) |
| 7 | ARQ task, if there's slow or fallible side work | [tasks](patterns/tasks.md) |
| 8 | Tests — happy path **and** each error code | [testing](testing.md) |

Steps 1 and 2 are one change. A model edit without its migration is an incomplete commit, not
a commit plus a follow-up.

## Schemas

Separate models per direction — don't reuse one class for input and output.

```python
class ThingCreate(BaseModel):     # request body
class ThingUpdate(BaseModel):     # PATCH — all fields optional
class ThingRead(BaseModel):       # response
    model_config = ConfigDict(from_attributes=True)
```

`ThingRead` is what the route returns via `model_validate`. Never return an ORM object
directly — the response shape has to be explicit, or it drifts the moment a column is added.

For list endpoints, define a `ThingListPage` — see [pagination](patterns/pagination.md).

## Route checklist

- `response_model=` set on every route.
- Auth dependency present unless the endpoint is genuinely public.
- Path/query params typed; `limit` clamped on list endpoints.
- **No `try`/`except`, no `HTTPException`.** The service raises a typed `AppError`; the global
  handler renders it — [errors](patterns/errors.md).
- No business logic. If there's an `if` that isn't about HTTP, move it down.
- Registered in the API aggregator with a prefix and tags.

## Wiring

- Register a new task function in the ARQ worker's function list — a task that isn't
  registered enqueues fine and never runs.
- A new setting goes in `Settings` and `.env.example` in the same commit.

## Before you say done

- `pytest` passes — paste the output.
- The migration applies cleanly from `head` and downgrades; `alembic check` is clean.
- Every error code the service can raise has a test that asserts the code.
- No `Any`, no local imports, no `commit()` in a service.

**See also:** [security](security.md) for anything touching auth, uploads, or personal data.
