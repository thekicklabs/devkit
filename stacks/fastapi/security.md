# FastAPI — Security

**Read when:** touching auth, permissions, file uploads, or personal data.

---

## Authorization lives in the service layer

The route proves *who* you are. The service proves *what you may touch*.

```python
async def get_application(
    db_session: CustomAsyncSession, *, application_id: uuid.UUID, user: User
) -> Application:
    result = await db_session.execute(
        select(Application).where(
            Application.id == application_id,
            Application.user_id == user.id,  # ownership is part of the query
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise ApplicationNotFound(application_id)
    return application
```

**Never trust a client-supplied owner id.** `user_id` comes from the authenticated principal,
never from the request body or a query param. Scope the ownership filter into the `WHERE` —
don't fetch then compare, which leaks existence through timing and error shape.

**"Not yours" raises the same `NotFound` as "doesn't exist".** A `Forbidden` tells an
attacker the row is real. Reserve 403 for surfaces where existence is not secret.

Every authz rule gets a test that proves the *denied* path.

## Sessions

- Cookie-based sessions are `httpOnly`, `secure` outside local, `SameSite=Lax`; the SPA is
  proxied same-origin so CORS stays empty.
- Set the cookie's `max_age` from the token's own `exp` — never recompute it from settings.
  A cookie outliving its token is a session that looks alive and 401s.
- Renewal is not revocation: a session version on the user row is re-checked on every
  request, so bumping it kills a live session immediately.
- A sliding session needs an absolute cap stamped once and carried unchanged through every
  renewal; a renewal that re-stamps it is a sliding session with no cap.
- Rotating `SECRET_KEY` logs everyone out — that is the point.

## Secrets and config

- Everything through `settings`. No literals, no `os.environ` reads scattered through modules.
- `.env` is never committed. A new setting goes to `.env.example` with a placeholder.
- No secret baked into a migration, a default argument, an image, or a job argument.
- `DEBUG` is verbosity only. Never gate a security control on it.
- Production mounts no `/docs`, `/redoc` or `/openapi.json`.

## Uploads

- **Validate content type and size server-side.** The client check is a convenience.
- **Never trust the filename.** Generate the stored key (UUID); keep the original name as a
  display-only column.
- Resolve the type from the extension against the caller's allow-list, then confirm the
  leading bytes really are that format. Reject anything executable.
- Store in private object storage. Serve through the API (or short-lived signed URLs) —
  never a permanent public link.
- Enforce ownership on both upload and download paths.
- **One implementation** (`core/upload_validation.py`). A new upload surface calls it; do
  not write a second copy.
- When the API serves user-supplied bytes: `X-Content-Type-Options: nosniff`, and
  `Content-Disposition: inline` for nothing but PDF and images.
- Copy filename, media type and size off the stored row, never from the download request —
  otherwise a caller chooses the `Content-Type` the file is served with.

## Personal data

- **Never log PII.** No emails, phone numbers, addresses, or document contents in log lines or
  exception messages. Log the row id. SQLAlchemy statement logging stays off even in `DEBUG`.
- Exceptions bubbling to the client must not carry a database error string — the
  `INTERNAL_ERROR` handler in [errors](patterns/errors.md) guarantees it.
- Contact details are not list data: no list response carries a phone number or contact
  email unless the schema that owns the rule names the exception.
- Consent is data, checked in the service — not a frontend checkbox the API takes on faith.
- Deletion requests reach uploaded files too, not just rows.

## Response caching

**Anything that answers differently per principal must not be stored by the caller.** Without
`Cache-Control: no-store` the browser's disk and back/forward caches hand a response to
whoever uses the machine next.

Declare it **once per router mount**, in one table, never per route: a mount is
`cacheable=True` or it gets the `no-store` dependency. A test asserts over the table, so a
route module nobody mounted fails the build. Only responses that return the same bytes to
every caller (health, config, reference data) are cacheable — adding to that set edits the
test too.

Streaming responses set the header themselves: FastAPI skips the dependency-header merge
when the endpoint returns its own response.

## Rate limiting and enumeration

- Key limits on the client address resolved from **one** trusted source (`core/network.py`):
  the socket peer, or a header the reverse proxy authenticates with a shared secret. Never
  raw `X-Forwarded-For`.
- Count against a bucket, not the raw address: IPv4 per address, IPv6 collapsed to its /64.
- Public account endpoints (registration, password reset, availability) get Redis-backed
  per-IP limits; password reset also a per-account window. Past it the request is accepted
  and silently does nothing — saying so is an account oracle.
- MFA verification and recovery use separate always-on per-account buckets that **fail
  closed** when Redis is unavailable.
- Decide deliberately which endpoints reveal account existence, document it, and keep
  `forgot-password` identical for registered, unknown, throttled and failed requests.

**See also:** [errors](patterns/errors.md) · [services & routes](patterns/services-routes.md) ·
[testing](testing.md)
