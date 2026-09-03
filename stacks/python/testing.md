# Python — Testing

**Read when:** writing or changing tests; before declaring any Python work done.

pytest. Tests must pass before you report done — paste the run, don't describe it.

---

## Layout

```
tests/
  conftest.py        shared fixtures, autouse mocks, factory imports
  factories/         one module per model / dataclass family
  test_<feature>.py  per feature, not per class
```

Test names say the behaviour: `test_register_rejects_duplicate_email`, not `test_register_2`.

## Mock external calls as reusable `autouse` fixtures

Nothing in the suite touches a real external service — HTTP, email, storage, queues.

```python
@pytest.fixture(autouse=True)
def sent_emails():
    sent = []

    async def _send(*, to, subject, html, text=None):
        sent.append({"to": to, "subject": subject, "html": html, "text": text})

    with patch("app.core.email.send_email", new=_send):
        yield sent
```

Put them in `conftest.py`. A mock patched inline in one test is a mock the next test forgets.
Capture rather than discard, so a test can assert on what was sent.

**Patch where the name is looked up.** Import the module, not the function, at the call
site (`from app.core import email as transport; transport.send_email(...)`) — binding
`send_email` at import time leaves the call site pointed at the real function after
`patch("app.core.email.send_email")`.

## Always use factories

Never hand-construct an object with more than a couple of fields in a test — the test
becomes about the setup, and every new field edits every test.

```python
user = await UserFactory.create_async(session=db_session)
user = await UserFactory.create_async(session=db_session, email="x@example.com")
```

The base factory supplies plausible defaults and creates required parents. **Pin every
constrained field** — a CHECK constraint, a partial unique index, a numeric range, an enum
whose random member is valid but wrong for the test — or the failure lands in a test about
something else. Every factory module is imported in `conftest.py`, or a factory discovered
by scanning subclasses is never found.

## Isolation

A test that passes alone and fails in the suite has shared state: a module-level cache, a
mock patched inline, a database row that was not rolled back. Fix the leak; never reorder
tests to hide it.

## Async

`pytest-asyncio` in `auto` mode. A fixture that needs `await` is `@pytest_asyncio.fixture`.
Never `asyncio.run` inside a test.

## Tools

```bash
uv run pytest path/to/test.py::test_name -x -vv     # one test, stop on first failure
uv run pytest --lf                                   # rerun last failures
uv run pytest -q                                     # the whole suite, before "done"
```

## Coverage expectations

| Kind | Must cover |
| --- | --- |
| Pure function | happy path · each branch · the boundary (empty, one, many, max) |
| Anything that raises | each distinguishable failure, asserted by its type or code |
| Anything authorised | the denied path, not only the allowed one |
| A bug fix | the regression test that failed before the fix |

**See also:** [typing](patterns/typing.md)
