# Pattern — ARQ background tasks

**Read when:** writing a background job, or deciding whether work belongs in one.
**Prereq:** [session](session.md)

---

## Two decorators, always both

```python
@arq_retry()
@arq_inject_db_session
async def post_match_task(ctx: dict, match_id: uuid.UUID):
    session = ctx["db_session"]

    match = await get_match_or_none(session, match_id=match_id)
    if match is None:
        raise JobExecutionFailed(f"Match not found: {match_id}")

    await create_notification(session, ...)

    # Follow-ups fire when this task's session commits
    add_to_arq_after_commit(session, "send_push_notification_task", match.user_id)
```

**No explicit `commit()` or `rollback()` in a task.** `arq_inject_db_session` handles it. The
task must be atomic — one task, one transaction.

## `arq_inject_db_session`

Tasks run outside HTTP request context, so they need their own session. This mirrors the
request lifecycle: commit on success, rollback on failure, always close.

```python
def arq_inject_db_session(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not args or args[0].get("job_id") is None:
            raise ValueError("Must be used for an arq task")

        if args[0].get("db_session") is not None:  # already injected (tests)
            return await func(*args, **kwargs)

        db_session = SessionLocal()
        args[0]["db_session"] = db_session
        try:
            result = await func(*args, **kwargs)
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise
        finally:
            await db_session.close()
        return result

    return wrapper
```

## `arq_retry`

Exponential backoff via `arq.Retry`. Exceptions in `ignore_exceptions` are permanent failures
and re-raise immediately instead of retrying.

```python
DEFAULT_IGNORE_EXCEPTIONS = [JobExecutionFailed]


def arq_retry(ignore_exceptions=None, with_exp_backoff=True):
    ignore_exceptions = (ignore_exceptions or []) + DEFAULT_IGNORE_EXCEPTIONS

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if any(isinstance(e, exc_type) for exc_type in ignore_exceptions):
                    raise
                delay = random.uniform(5, 10)
                if with_exp_backoff:
                    delay = delay * (2 ** args[0]["job_try"])
                logger.exception("task failed, retrying")
                raise Retry(defer=delay) from e

        return wrapper

    return decorator
```

**Raise `JobExecutionFailed` for anything retrying can't fix** — a missing row, an invalid
id, a permanently rejected payload. Retrying those just burns the queue.

## A job somebody is waiting on must reach a terminal status

When a row is the contract a browser polls — an export, a report — every way of failing has
to end at a status the browser can read. An exception rolls the task's transaction back, so a
failure written on the way out is a failure that never happened. Two rules:

1. **Take the last try as an argument and write the failure there.** `ctx["job_try"]` is
   arq's attempt counter. Past a ceiling the service stops attempting the work and records
   the outcome instead, on a call that returns normally and therefore commits.
2. **Count confirmed missing hand-offs on the row, not scans or runs.** A worker killed
   mid-job leaves the row as the recovery scan found it, so a counter the job increments is a
   counter it can lose. Check the deterministic job's ARQ status first: queued, deferred and
   in-progress jobs are live and must not consume an attempt.

A status the job writes and then overwrites in the same transaction is not observable —
don't write it, and don't index for it.

**Never pass a secret as a job argument.** arq logs job arguments (truncated, not
disableable). Pass the row id and read the secret inside the task.

## Queuing from a service

```python
add_to_arq_after_commit(db_session, "process_media_task", media.id, _queue_name=HEAVY_QUEUE)
```

**Why `after_commit` is the default:** if the request rolls back, the row never existed — a
job enqueued before commit would fire and fail looking for it.

Use `add_to_arq_before_commit` only when a failure to enqueue should fail the request.

For a recoverable side effect, use a deterministic `_job_id` and reconcile from the
persisted source rows: a database commit followed by a Redis failure otherwise leaves
durable state with no job. A recovery task at worker startup and on a cron selects only live
rows still needing the work; the stable job id makes that scan safe to repeat.

**Idempotent producers.** Where a task creates a row that must exist once per event, give
the table a `UNIQUE (owner_id, dedupe_key)` and let the insert return `None` on conflict so
the caller no-ops. The key must vary with anything that makes the event genuinely new (a
timestamp for a repeatable transition), and be scoped to the owner, never global.

## What belongs in a task

Email and notification delivery · file/document processing · external API calls · anything
slow enough to hurt p95 · anything that may fail independently of the request.

**Not** in a task: anything the response body depends on.

**See also:** [session](session.md) · [testing](../testing.md) · [debug](../debug.md)
