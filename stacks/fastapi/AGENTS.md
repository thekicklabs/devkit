---
name: fastapi
description: FastAPI + SQLAlchemy 2 async + Alembic + ARQ — layout, request lifecycle, errors, testing
route: FastAPI / SQLAlchemy backend
requires: [python]
---
# FastAPI — router

**Read when:** any task touching the API.
**Prereq:** [`../python/AGENTS.md`](../python/AGENTS.md) · `../workflow.md`

FastAPI · SQLAlchemy 2 async (raw — **no SQLModel**) · PostgreSQL · Alembic · ARQ + Redis ·
Pydantic v2 · pytest + pytest-asyncio · polyfactory.

## Layout

```
app/
  api/             GATEWAY ONLY — deps, router, routes/
  tasks/           GATEWAY ONLY — ARQ entry points
  services/        ALL business logic, as <feature>/<action>.py
  models/          SQLAlchemy declarative models
  schemas/         Pydantic request/response models
  core/            db, session, config, errors, error_codes, arq, pagination, security
  main.py          app factory, error handlers, router mounted at /api
  worker.py        ARQ WorkerSettings — the task registry
alembic/versions/
tests/             conftest, factories/, per-feature test modules
```

One operation per service module; `api/` and `tasks/` only translate to and from HTTP and job
semantics — see [service modules](patterns/service-modules.md).

## Routing

| Doing… | Read |
| --- | --- |
| Adding an endpoint / model / task | [`feature.md`](feature.md) |
| Raising, mapping or documenting an error | [`patterns/errors.md`](patterns/errors.md) |
| Writing or fixing tests | [`testing.md`](testing.md) |
| Restructuring existing code | [`refactor.md`](refactor.md) |
| Auth, permissions, uploads, personal data | [`security.md`](security.md) |
| Slow query, N+1, load | [`performance.md`](performance.md) |
| Chasing a bug | [`debug.md`](debug.md) |
| Reviewing a diff | [`review.md`](review.md) |

**Patterns** (read the ones your task touches):
[service modules](patterns/service-modules.md) · [services & routes](patterns/services-routes.md) ·
[errors](patterns/errors.md) · [session](patterns/session.md) · [models](patterns/models.md) ·
[migrations](patterns/migrations.md) · [data migrations](patterns/data-migrations.md) ·
[append-only](patterns/append-only.md) · [tasks](patterns/tasks.md) · [emails](patterns/emails.md) ·
[pagination](patterns/pagination.md) · [caching](patterns/caching.md) ·
[factories](patterns/factories.md)

## Non-negotiables

1. **Services never call `commit()`.** The request lifecycle commits. Use `flush()` for an id,
   and only then — see [session](patterns/session.md).
2. **Routes hold no business logic.** Extract params, call a service, serialize, return. The
   same goes for tasks. Business rules live in `services/`, one operation per file.
3. **Services raise `AppError` subclasses; one global handler renders them.** No
   `HTTPException` in application code — [errors](patterns/errors.md).
4. **A column change ships with its Alembic migration in the same commit.** Nothing in CI
   diffs models against the DB — drift fails silently in production.
5. **Every user-facing list endpoint is cursor-paginated** — [pagination](patterns/pagination.md).
6. **Authorization lives in the service, ownership in the `WHERE`** — [security](security.md).

## Before you say done

```bash
uv run ruff format . && uv run ruff check . && uv run ty check
uv run alembic check          # models and migrations agree
uv run pytest -q
```

Paste the run. `pytest` needs a live PostgreSQL and Redis — the suite creates
`<POSTGRES_DB>_test`, rebuilds the schema per session and rolls every test back inside a
SAVEPOINT. Compose-first projects run these as `docker compose exec api …` — see the
`compose` stack.
