---
name: plan
description: Interrogate a request before writing code — restate it, surface assumptions and the readings that would produce different work, write the plan, confirm. Use at the start of anything non-trivial, or whenever the request could be read two ways.
---

# Plan

Do not write code yet. The cheapest bug is the one caught before the first line.

## 1. Restate

One paragraph, your words: what is being asked, for whom, and what "done" looks like. If you
cannot write this, you do not understand the request — ask.

## 2. Read what already exists

Read the routed rule files for the stack, then the code the change touches. Look for the
existing thing first: a helper, a service, a component. A convention you invent is one
someone has to undo.

## 3. Assumptions and seams

List every assumption you are making. Name the seams — the module boundaries, public
functions, endpoints, or components the change goes through. These are where the tests will
attach (`tdd` skill) and where the diff will be reviewed.

## 4. The readings that diverge

Find the 2–3 ways the request could be read that would produce *materially different* work.
For each: what you'd build, what it costs, what it forecloses.

- If one reading is obviously right, take it and say which you took.
- If they genuinely diverge, **stop and ask** — one question, options listed, your
  recommendation first.

Also ask before: a new dependency · a contract change that breaks the other side · anything
touching auth, payments, or personal data · deleting or overwriting existing work · departing
from a rule in the routed files.

## 5. Write the plan

Ordered steps, each naming the files it touches and the rule file that governs it. Include
the verification step: the exact commands that prove it works. Note anything adjacent you
noticed and are *not* fixing.

## 6. Confirm

Present the plan. Wait for a yes before building unless the request already said "just do
it" and no reading diverged.
