---
name: debug
description: Chase a bug by reproducing it in a failing test first, reading the actual failure, and shipping the fix with its regression test in one change. Use when something is broken, flaky, or "works on my machine".
---

# Debug

A fix without a failing-then-passing test is a guess.

## 1. Reproduce

Turn the report into a failing test at the nearest public seam. If you cannot reproduce it,
say so — do not fix what you cannot see fail. For a flaky test, run it ten times in a loop
before touching anything.

## 2. Read the failure

Read the whole traceback, the actual assertion, the actual log line. Do not guess from the
symptom. The stack's `debug.md` under `AGENTS/<stack>/` has a symptom → cause table for the
failures that have already bitten; check it before forming a theory.

## 3. Narrow

Bisect: half the input, half the code path, one variable at a time. Confirm the cause with
evidence — a print you then remove, a debugger, a query run directly — not with reasoning
alone.

## 4. Fix

The smallest change that addresses the cause, not the symptom. If the fix touches a
convention, update its rule file. If the real cause is somewhere else than reported, say
that, and fix it there.

## 5. Prove

The test from step 1 passes; the whole suite passes; paste both. Fix and regression test are
one commit.

## Do not

- Add a retry, a sleep, or a broader `except` to make a symptom go away.
- Change the test's expectation to match the bug.
- Leave `echo=True`, `console.log`, or `print` behind.
