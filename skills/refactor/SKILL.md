---
name: refactor
description: Restructure code without changing behaviour — same tests green before and after, unchanged; one refactor per commit, never mixed with a feature. Use when asked to clean up, extract, rename, or move code.
---

# Refactor

**Behaviour-preserving only.** If what an endpoint returns, what a component renders, or
when a job fires changes, it is a feature — plan and test it as one.

## Discipline

1. The existing suite passes **before** you start. If it doesn't, that is the task.
2. Refactor.
3. The same tests, unchanged, still pass. Paste the run.

If you had to edit a test to make it green, behaviour changed. Stop and say so.

## Sequencing

One refactor per commit, separate from feature work. A diff that both moves code and changes
it cannot be reviewed.

Small moves in order: rename → extract → move → delete. Each independently green.

## Deliberate boundaries are not gaps

Every stack has architectural choices that look like something to "improve" — a missing
layer, a function that could be a class, a duplicate that could be abstracted. The stack's
`refactor.md` under `AGENTS/<stack>/` lists them. Read it first; if one genuinely blocks you,
raise it rather than routing around it.

## Not a refactor

Anything that changes persisted shape (a column, a route path, a query key, a public
signature other code imports) is a behaviour change with a migration or a compatibility
story. Confirm before writing that.
