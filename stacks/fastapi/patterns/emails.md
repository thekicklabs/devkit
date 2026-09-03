# Pattern — emails

**Read when:** adding an email, changing one's copy, or touching delivery transport.
**Prereqs:** [service modules](service-modules.md) · [tasks](tasks.md)

Three layers, and they do not overlap:

| Layer | File | Knows about |
| --- | --- | --- |
| Transport | `app/core/email.py` | The provider (API or SMTP). Not what any message says |
| Message | `app/services/email/<action>.py` | A subject, a template, a context |
| Delivery decision | `app/tasks/email.py` | Retry-or-fail. Nothing else |

---

## The class-in-`services/` exception

[service modules](service-modules.md) says one public async function per module, and
[refactor](../refactor.md) says services are functions, not classes. **Email classes are the
one exception**, and its boundary is exact:

- An email class is a *message object* — a subject, a template name, and the variables that
  template needs. It holds no domain policy, makes no decisions, and touches no session.
- It lives beside the service function that sends it: `send_welcome.py` exports
  `WelcomeEmail` **and** `send_welcome_email()`. Two names, one message, one file.
- Nothing else in `services/` gets a class.

## Adding an email

```python
class WelcomeEmail(BaseEmail):
    template = "welcome.html"

    def __init__(self, *, user: User) -> None:
        super().__init__(to=user.email)
        self._user = user

    @property
    def title(self) -> str:
        return "Welcome"

    @property
    def context(self) -> dict[str, Any]:
        return {"full_name": self._user.full_name}
```

`BaseEmail` supplies `render()` and `send()`. `render()` is **sync** — templating is
CPU-only, and an `await` that never yields misrepresents it as I/O. A `shared_context()`
merges product name, base URL and support address under every template, so no template
hardcodes them.

## Templates

Every one extends `base.html`; shared fragments are macros. Mail clients are not browsers:
tables, not flexbox; inline styles; no webfonts; one remote image at most, with alt text.
Colours are design tokens resolved to hex.

The environment uses `StrictUndefined`: a context key a template references but the class
stopped providing **raises** instead of rendering a blank. A test renders every email, which
turns that into a build failure.

## Transport

```python
from app.core import email as transport

await transport.send_email(to=..., subject=..., html=...)
```

Import the **module**, never the function, so the autouse test fixture's patch is what the
call site sees.

- **Suppression is the local and test default:** an empty API key / SMTP host logs and
  returns without delivery, so nothing reaches a provider by accident.
- A transport failure is **not** a `JobExecutionFailed`. A refused connection, a greylisting
  4xx and a rate limit are transient; the retry ladder handles them.
- **Never log an address or subject.** A subject can be user-authored. Log a row id.

## Sending one

Emails are always a background job, never inline in a request — [tasks](tasks.md).

```python
add_to_arq_after_commit(db_session, "send_welcome_email_task", user.id)
```

**Never put a secret in a job argument** — a reset token travels as the row id, and the task
reads the secret off the row. Delivery is at-least-once: provider success followed by a
commit failure leaves the work available for retry, so the recipient can receive a
duplicate. Design the copy for that.

**See also:** [service modules](service-modules.md) · [tasks](tasks.md) ·
[security](../security.md)
