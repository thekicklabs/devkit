# Pattern — session, hooks, and the request lifecycle

**Read when:** writing any service, or any code that needs work to happen at commit time.

The whole request is one transaction. Either everything commits or nothing does. Services
never call `commit()` themselves.

---

## `CustomAsyncSession`

`AsyncSession.commit()` is overridden to run four kinds of hook. Nothing fires until the
transaction actually commits — that is the point.

```python
class CustomAsyncSession(AsyncSession):
    async def handle_before_commit_hooks(self) -> None:
        for callback in getattr(self, "before_commit_callbacks", []):
            result = callback()
            if isinstance(result, Awaitable):
                await result

    async def handle_after_commit_hooks(self) -> None:
        for callback in getattr(self, "after_commit_callbacks", []):
            result = callback()
            if isinstance(result, Awaitable):
                await result

    async def handle_before_commit_to_queue_hooks(self) -> None:
        for job in getattr(self, "before_commit_arq_jobs", []):
            arq_redis = await get_arq_redis()
            await arq_redis.enqueue_job(job["job_name"], *job["args"], **job["kwargs"])

    async def handle_after_commit_to_queue_hooks(self) -> None:
        for job in getattr(self, "after_commit_arq_jobs", []):
            arq_redis = await get_arq_redis()
            await arq_redis.enqueue_job(job["job_name"], *job["args"], **job["kwargs"])

    async def commit(self) -> None:
        try:
            await self.handle_before_commit_hooks()
            await self.handle_before_commit_to_queue_hooks()
            await super().commit()
        except Exception:
            await self.rollback()
            raise
        else:
            try:
                await self.handle_after_commit_hooks()
                await self.handle_after_commit_to_queue_hooks()
            except Exception:
                logger.exception("after-commit hook failed")
                await self.rollback()
                raise
        finally:
            self.after_commit_callbacks: list[Callable[[], Any]] = []
            self.before_commit_callbacks: list[Callable[[], Any]] = []
            self.before_commit_arq_jobs: list[dict[str, Any]] = []
            self.after_commit_arq_jobs: list[dict[str, Any]] = []
```

## Choosing a hook

| Hook | Runs | On failure |
| --- | --- | --- |
| `add_before_commit_callback` | Before `COMMIT` | Request errors, transaction rolls back |
| `add_after_commit_callback` | After `COMMIT` succeeds | Logged, no rollback — data is already committed |
| `add_to_arq_before_commit` | Enqueue before `COMMIT` | Request errors, transaction rolls back |
| `add_to_arq_after_commit` | Enqueue after `COMMIT` succeeds | Logged only |

**Default to `after_commit`** for side effects — notifications, emails, external API calls,
background processing. Use `before_commit` only when the side effect is essential to the
request being correct.

## Registering hooks

Each helper lazily creates its list, so services just call them:

```python
def add_before_commit_callback(db_session, callback: Callable[[], Awaitable[None]]) -> None: ...
def add_after_commit_callback(db_session, callback: Callable[[], Awaitable[None]]) -> None: ...
def add_to_arq_before_commit(db_session, job_name: str, *args, **kwargs) -> None: ...
def add_to_arq_after_commit(db_session, job_name: str, *args, **kwargs) -> None: ...
```

## Session lifecycle — auto commit/rollback per request

```python
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,  # explicit control over when flushes happen
    expire_on_commit=False,  # objects stay usable after commit, no re-fetch
    bind=engine,
    class_=CustomAsyncSession,
)


async def get_session(request: Request) -> AsyncGenerator[CustomAsyncSession, None]:
    session = SessionLocal()
    request.state.db_session = session
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


SessionDep = Annotated[CustomAsyncSession, Depends(get_session)]
```

## `autoflush=False` — two consequences

A service that reads back what it just added must `flush()` first: new rows are invisible
to any `select()` until flushed, and `execute(delete(...))` fires immediately without
flushing pending ORM state, so delete-then-re-add is the shape to watch. Mutations to already
persistent rows are safe — a re-`select()` by primary key returns the identity-mapped
instance with its dirty attributes.

No unnecessary flushes either: flush when an id or a database-computed value is needed, or
for the read-back above. Not "just in case".

## Full request lifecycle

```
Request arrives
  -> get_session creates CustomAsyncSession
  -> Route handler runs (thin — just calls services)
    -> Services do business logic, session.add() / flush()
    -> Services register hooks: add_to_arq_after_commit(session, ...)
  -> get_session calls session.commit()
    -> before_commit_callbacks       (fail = rollback + error response)
    -> before_commit ARQ enqueue     (fail = rollback + error response)
    -> COMMIT
    -> after_commit_callbacks        (fail = logged only)
    -> after_commit ARQ enqueue      (fail = logged only)
    -> hook lists cleared
  -> Response

Any exception during the request (including an AppError):
  -> rollback — no hooks fire, no ARQ jobs enqueue
```

## Engine

```python
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_size=10,
    connect_args={"prepared_statement_cache_size": 0},
)
```

`prepared_statement_cache_size=0` is not optional. Without it, connections alive across a
migration reuse cached statements referencing old column positions — silent data corruption.

**See also:** [tasks](tasks.md) · [services & routes](services-routes.md) · [testing](../testing.md)
