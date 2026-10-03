---
name: tdd
description: Build test-first in vertical slices — red, green, refactor — through public seams agreed up front. Use when asked to work test-first, when adding behaviour to code with an existing suite, or when a change is easy to get subtly wrong.
---

# TDD

## Agree the seams first

Before the first test, name the public seam the behaviour is observed through: an endpoint,
an exported function, a component's rendered output. Tests attach there — never to private
helpers or to the shape of the implementation. If the seam does not exist yet, agree its
signature (the `plan` skill does this).

## The loop

1. **Red** — write one test for one behaviour. Run it. Watch it fail *for the right reason*
   and quote the failure, not the assertion line: an import error, an exception, and the
   predicted mismatch all print red, and only the predicted mismatch proves the test
   measures the behaviour.
2. **Green** — the smallest change that passes. Ugly is fine here.
3. **Refactor** — with the suite green, clean up. Tests unchanged. Run again.

One slice at a time, thinnest vertical slice first: the happy path end to end before any
edge case.

## What a test must not be

- **Tautological** — asserting the mock returned what you told it to return.
- **Implementation-coupled** — breaking when a private function is renamed or a call
  count changes, while behaviour is identical.
- **A snapshot** — passing until it doesn't, then re-recorded without being read.
- **Order-dependent** — passing alone, failing in the suite.

## What to cover

Happy path · each distinguishable failure (asserted by its code/message, not just its
status) · the boundary (empty, one, many, max) · the denied path for anything authorised.

If your router links a stack `testing.md`, it says how tests are set up (fixtures,
factories, mocks, isolation). Read it before the first test.

## When a failing test is impractical

If the only test would need broad harness setup, brittle mocks, production-only state, or
large unrelated fixture churn, use the closest executable check instead — a targeted script,
a reproduction command, a focused integration run — and say so. No new test beats a bad one.
Never change a test to match a wrong implementation, or weaken an assertion, unless the
expected behaviour genuinely changed.

## Done

The whole suite green, pasted. Every new behaviour has a test that failed before the change,
or a stated reason and the closest check you ran instead.
