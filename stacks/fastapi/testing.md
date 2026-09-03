# FastAPI — Testing

**Read when:** writing or changing API tests; before declaring any backend work done.
**Prereqs:** [`../python/testing.md`](../python/testing.md) · [session](patterns/session.md)

**Every endpoint gets at least a happy path, the denied path, and each error code it can
raise.** Tests must pass before you report done — paste the run, don't describe it.

---

## No commits in tests — SAVEPOINT isolation

Each test runs inside a nested transaction. When it ends, the outer transaction rolls back and
the data vanishes. No `TRUNCATE`, no cleanup fixtures.

```python
@pytest_asyncio.fixture
async def db_session(create_test_database):
    conn = await test_engine.connect()
    txn = await conn.begin()
    session = TestAsyncSession(bind=conn, expire_on_commit=False, autoflush=False)

    await conn.begin_nested()

    # After each SAVEPOINT ends, start a new one, so a commit() inside application
    # code only commits the SAVEPOINT — never the outer transaction
    @event.listens_for(session.sync_session, "after_transaction_end")
    def restart_savepoint(_sync_session, _transaction):
        if conn.closed:
            return
        if not conn.in_nested_transaction():
            conn.sync_connection.begin_nested()

    yield session

    await session.close()
    await txn.rollback()
    await conn.close()
```

Database setup is session-scoped: create the DB if absent, `DROP SCHEMA public CASCADE` +
recreate, `Base.metadata.create_all()`, dispose at the end.

## The fixture session mirrors `SessionLocal` — `autoflush=False`

The fixture matches production so the suite can fail on a missing flush instead of hiding
one. Two rules follow:

**A service that reads back what it just added must `flush()`** — [session](patterns/session.md).

**A test that calls a service directly and then asserts with SQL must `flush()` itself.** No
request means no commit, and services that nothing reads back in-request correctly never
flush.

The `client` fixture's `get_session` override commits, as the real dependency does, but inside
a savepoint it opens per request — so a 4xx/5xx unwinds only the request, exactly as
production's per-request transaction does, and the rows the test's factories created survive.

## `TestAsyncSession` — capture hooks, don't fire them

```python
class TestAsyncSession(CustomAsyncSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.after_commit_callbacks = []
        self.before_commit_callbacks = []
        self.before_commit_arq_jobs = []
        self.after_commit_arq_jobs = []

    # Straight back to the plain implementation: hooks are recorded, never fired.
    async def commit(self):
        await super(CustomAsyncSession, self).commit()
```

Assert on **intent**:

```python
async def test_creates_background_job(db_session):
    await create_media(db_session, media_in=...)
    assert any(job["job_name"] == "process_media_task" for job in db_session.after_commit_arq_jobs)
```

Assert the job was registered — not that the side effect happened. The side effect is the
worker's job and belongs in the task's own test.

## Errors

Assert the code, not only the status:

```python
response = await client.get(f"/api/applications/{other_users_application.id}")
assert response.status_code == 404
assert response.json()["error"]["code"] == "APPLICATION_NOT_FOUND"
```

## Coverage expectations

| Kind | Must cover |
| --- | --- |
| Endpoint | happy path · 401 unauthenticated · the not-yours path · each `AppError` code · 422 invalid body |
| List endpoint | first page · cursor to page 2 · last page `next_cursor=None` · no dupes on tied sort keys |
| Service registering a hook | the right job/callback is in the right list |
| ARQ task | happy path · the `JobExecutionFailed` branch |
| Migration | the suite runs against the new schema; `alembic check` clean |
| Error handlers | envelope shape · `INTERNAL_ERROR` leaks nothing |

**See also:** [factories](patterns/factories.md) · [feature](feature.md) · [tasks](patterns/tasks.md) ·
[pagination](patterns/pagination.md) · [errors](patterns/errors.md)
