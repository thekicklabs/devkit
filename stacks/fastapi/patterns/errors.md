# Pattern — errors

**Read when:** a service can fail in a way the caller must distinguish; adding or changing an
error response; writing a frontend that switches on failures.

Services raise. One handler renders. The client reads a **code**, never a status.

---

## The base class

```python
# app/core/errors.py
class AppError(Exception):
    error_code: ErrorCode
    status_code: int = 400

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Mapping[str, object] | str | None = None,
    ) -> None:
        super().__init__(message or self.error_code.value)
        self.message = message or self.error_code.value
        self.details = details


class NotFound(AppError):
    error_code = ErrorCode.NOT_FOUND
    status_code = 404


class Forbidden(AppError):
    error_code = ErrorCode.FORBIDDEN
    status_code = 403


class Conflict(AppError):
    error_code = ErrorCode.CONFLICT
    status_code = 409


class ValidationFailed(AppError):
    error_code = ErrorCode.VALIDATION_FAILED
    status_code = 422
```

Every domain exception subclasses one of these and pins its own code:

```python
# app/services/application/get.py
class ApplicationNotFound(NotFound):
    error_code = ErrorCode.APPLICATION_NOT_FOUND

    def __init__(self, application_id: uuid.UUID) -> None:
        super().__init__(details={"application_id": str(application_id)})
```

Declared next to the function that raises it, per [service modules](service-modules.md).

## Services raise

```python
async def get_application(db_session, *, application_id, user) -> Application:
    result = await db_session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise ApplicationNotFound(application_id)
    return application
```

Not `-> Application | None` with the route deciding what `None` means. The service knows
*why* it cannot proceed; the route does not, and should not have to. "Not yours" and
"doesn't exist" raise the **same** exception — see [security](../security.md).

A route therefore has nothing to map:

```python
@router.get("/applications/{application_id}", response_model=ApplicationRead)
async def read_application(session: SessionDep, user: CurrentUser, application_id: uuid.UUID):
    application = await get_application(session, application_id=application_id, user=user)
    return ApplicationRead.model_validate(application)
```

`HTTPException` is not used in application code. If you are writing one, a domain
exception is missing.

## Error codes are one enum, documented in one table

```python
# app/core/error_codes.py
class ErrorCode(str, Enum):
    NOT_FOUND = "NOT_FOUND"
    ...
```

| Code | Status | When | `details` shape |
| --- | --- | --- | --- |
| `NOT_FOUND` | 404 | Generic missing resource | — |
| `FORBIDDEN` | 403 | Authenticated, not allowed, and existence is not secret | — |
| `CONFLICT` | 409 | State prevents the write (already submitted, version mismatch) | `{"current": …}` |
| `VALIDATION_FAILED` | 422 | Body/params failed domain validation beyond the schema | `[{"field", "code", "message"}]` |
| `RATE_LIMITED` | 429 | Bucket exhausted | `{"retry_after_seconds": n}` |
| `INTERNAL_ERROR` | 500 | Anything unexpected | — |
| `<FEATURE>_<REASON>` | pinned by the subclass | e.g. `APPLICATION_NOT_FOUND`, `EMAIL_ALREADY_REGISTERED` | documented on the row |

**Adding a code is an edit to this table** (the project's copy of it, in `project.md` or beside
`error_codes.py`), the enum, and a subclass — in that order, one commit. The frontend's
`errors` translation namespace is the same list; a code without a translation is a
review-blocking finding on either side.

## One handler

```python
# app/main.py
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.error_code.value, "message": exc.message, "details": exc.details}
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR.value,
                "message": "Internal error",
                "details": None,
            }
        },
    )
```

The envelope is always `{"error": {"code", "message", "details"}}`. The second handler never
echoes the exception: a database error string leaks column names and values.

Pydantic's `RequestValidationError` gets a third handler that renders it as
`VALIDATION_FAILED` with the field list in `details` — and does **not** echo submitted
values.

## The client switches on `code`

Status is transport. A 409 means "state conflict" to a proxy; `APPLICATION_ALREADY_SUBMITTED`
means something to a user. The frontend renders `t(\`errors.${code}\`)` and branches on the
code where behaviour differs — never on `response.status`.

## Tests

- Every distinguishable failure asserts the **code**: `assert body["error"]["code"] ==
  "APPLICATION_NOT_FOUND"`. Asserting only `status_code == 404` proves nothing about which
  failure it was.
- The handlers have their own tests: an `AppError` renders the envelope with its status; a
  raw `Exception` renders `INTERNAL_ERROR` with no message from the exception.

**See also:** [services & routes](services-routes.md) · [security](../security.md) ·
[testing](../testing.md)
