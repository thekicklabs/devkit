---
name: debug
description: Chase a bug by reproducing it in a failing test first, reading the actual failure, and shipping the fix with its regression test in one change. Use when something is broken, flaky, or "works on my machine".
---

# Debug

A fix without a failing-then-passing test is a guess. Every line you ship traces to evidence;
a change that "might help" is a hypothesis, not a fix.

## 1. Reproduce

Turn the report into a failing test at the nearest public seam. Reproduce it yourself on the
surface where it was reported, through kick-mode's [driver](../kick-mode/SKILL.md#done),
before asking the user to; ask only with a specific reason you cannot reach that surface. If
it will not fire, synthesize the trigger, tighten the conditions, or instrument until it
does. If you still cannot see it fail, say so — do not fix what you cannot see fail. For a
flaky test, run it ten times in a loop before touching anything.

## 2. Read the failure

Read the whole traceback, the actual assertion, the actual log line. Do not guess from the
symptom. If your router links a stack `debug.md`, check its symptom → cause table before
forming a theory.

## 3. Narrow

List the candidate causes, then rule them out until one survives. The `how` skill grounds
them in the subsystem; `why` finds the regression history. Each pass, take the split that
cuts the most: half the input, half the code path, one variable at a time. Confirm the
surviving mechanism with evidence — a print you then remove, a debugger, a query run
directly — not with reasoning alone. When evidence refutes a hypothesis, revert what it
motivated.

## 4. Fix

The smallest change that addresses the cause, not the symptom. If the fix crosses a function
boundary, sketch it with `architect` first. If the fix touches a convention, update its rule
file. If the real cause is somewhere else than reported, say that, and fix it there.

## 5. Prove

The test from step 1 passes, the original reproduction passes on the same surface, and the
whole suite passes; paste them. "Inconclusive" or a different surface is not a pass. Fix and
regression test are one commit.

## Do not

- Add a retry, a sleep, or a broader `except` to make a symptom go away.
- Change the test's expectation to match the bug.
- Leave `echo=True`, `console.log`, or `print` behind.

## Report

What was broken, the root cause, the fix, and how you verified it. Quote the decisive failing
and passing output, trimmed to the assertion and the counts.
