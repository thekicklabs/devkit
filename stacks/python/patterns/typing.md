# Pattern — typing

**Read when:** writing any annotated Python; when tempted by `Any`, a `cast`, or `# type: ignore`.

`ty` checks the tree, and it is part of "done". Types are documentation the checker reads.

---

## Rules

- **No `Any`** unless the value is genuinely any type — a JSON blob you forward untouched,
  a `**kwargs` you pass straight through. "I didn't know the type" is not that.
- **`object` over `Any`** for "I accept anything and will not touch it".
- **No unexplained suppression.** `# type: ignore[code]` with the specific code and a
  trailing reason, or nothing. A bare `# type: ignore` is a bug with a blindfold.
- **`cast` is an assertion you have proved.** Prefer narrowing (`isinstance`, `assert x is
  not None`) that the checker can follow.
- **Modern syntax:** `list[str]`, `X | None`, `from __future__ import annotations` only when
  a forward reference genuinely needs it.
- **Return types on every public function.** `-> None` included.

## Shapes

| Need | Use |
| --- | --- |
| A value that is one of a fixed set | `Enum` (`str, Enum` when it crosses a wire) |
| A structured record | `@dataclass(frozen=True)` or a pydantic model at a boundary |
| "Anything with these methods" | `Protocol`, not an ABC the caller must inherit |
| A dict with known keys | `TypedDict` — or better, a dataclass |
| Optional | `X | None`, and handle the `None` where it arises |

## Boundaries

Parse at the edge, trust inside. A pydantic model validates the request body once; the
service takes typed arguments and never re-checks. Untyped data (`dict[str, Any]`) does
not travel further than the function that parsed it.

## Keyword-only after the first argument

```python
async def create_thing(db_session: Session, *, thing_in: ThingCreate, user: User) -> Thing:
```

Positional arguments beyond the first are a call site that silently breaks on reordering.
