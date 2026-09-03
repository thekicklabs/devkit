---
name: python
description: uv · ruff · ty · pytest — toolchain, typing and testing rules for any Python code
route: Python code
---
# Python — router

**Read when:** any task touching Python code.
**Prereq:** `../workflow.md`

**uv** for dependencies and running · **ruff** for lint and format · **ty** for types ·
**pytest** for tests. Nothing is installed with `pip`; `uv.lock` is committed and `uv sync`
is reproducible.

## Routing

| Doing… | Read |
| --- | --- |
| Writing or fixing tests | [`testing.md`](testing.md) |
| Type annotations, `Any`, protocols, generics | [`patterns/typing.md`](patterns/typing.md) |
| Web API on FastAPI | `../fastapi/AGENTS.md` (when installed) |

## Running it

```bash
uv sync                        # .venv from the lockfile
uv run <cmd>                   # every command runs through uv
uv add <package>               # runtime dependency — ask first
uv add --dev <package>         # tooling and tests
```

`uv add` rewrites `uv.lock`, which belongs in the same commit.

## Settings

Every value reaches the app through one `settings` object (pydantic-settings). No
`os.environ` anywhere else, no literals. **A new setting is added to `.env.example` with a
placeholder in the same commit** — `.env` itself is never committed.

`list`-typed settings need `Annotated[..., NoDecode]` plus a `mode="before"` validator, or
pydantic-settings JSON-parses the raw env var and a comma-separated value raises before the
validator can split it.

## Non-negotiables

1. **No `Any`** unless the value is genuinely any type — [typing](patterns/typing.md).
2. **No local imports** unless breaking a real circular dependency. If you hit one, the
   module boundary is wrong; fix that.
3. **`datetime.now(timezone.utc)`** — never `datetime.utcnow()`, never a naive datetime.
4. **Factories, not hand-built fixtures**, for anything with more than two fields —
   [testing](testing.md).
5. **External calls are mocked as `autouse` fixtures in `conftest.py`**, never inline in a
   test.
6. **No `print` for diagnostics** in library code. `logging`, with the module logger.

## Before you say done

```bash
uv run ruff format .
uv run ruff check .
uv run ty check
uv run pytest -q
```

Paste the run.
