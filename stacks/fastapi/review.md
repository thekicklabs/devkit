# FastAPI — Review

**Read when:** reviewing a backend diff, after the generic `code-review` skill checklist.

---

## Blocking

- [ ] **Model changed without a migration in the same commit?** — [migrations](patterns/migrations.md)
- [ ] **A longer enum/status value added without widening the real `VARCHAR(n)` first?**
- [ ] **`commit()` or `rollback()` called inside a service or a task?** — [session](patterns/session.md)
- [ ] **Business logic in a route?** Any `if` that isn't about HTTP — [services & routes](patterns/services-routes.md)
- [ ] **`HTTPException`, or a `try`/`except` in a route?** — [errors](patterns/errors.md)
- [ ] **A new failure without an error code, or a code without a test asserting it?** — [errors](patterns/errors.md)
- [ ] **A user-facing list endpoint that isn't cursor-paginated?** — [pagination](patterns/pagination.md)
- [ ] **Ownership filter missing, or an owner id taken from the request?** — [security](security.md)
- [ ] **New endpoint without the denied path tested?** — [testing](testing.md)

## Should fix

- [ ] `Any` introduced where a real type exists · local import not breaking a genuine cycle
- [ ] `== True` / `== None` instead of `.is_(...)` — [models](patterns/models.md)
- [ ] `datetime.utcnow()` instead of `datetime.now(timezone.utc)`
- [ ] Model hand-constructed in a test instead of via a factory — [factories](patterns/factories.md)
- [ ] External call not mocked as an `autouse` fixture
- [ ] Relationship accessed in a loop without `selectinload` — [performance](performance.md)
- [ ] Side effect done inline where it should be an `after_commit` hook
- [ ] New ARQ task not registered in the worker's function list
- [ ] `response_model` missing on a route · `limit` unclamped on a list route
- [ ] PII in a log line or exception message — [security](security.md)
- [ ] A flush with no reader — [session](patterns/session.md)
- [ ] Secret passed as a job argument — [tasks](patterns/tasks.md)

## Worth asking about

- [ ] A repository layer or service-class abstraction creeping in — [refactor](refactor.md)
- [ ] A new setting without its `.env.example` line

**See also:** [refactor](refactor.md) · [security](security.md)
