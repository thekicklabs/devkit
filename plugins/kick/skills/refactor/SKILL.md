---
name: refactor
description: Restructure code without changing behaviour — same tests green before and after, unchanged; one refactor per commit, never mixed with a feature. Use when asked to clean up, extract, rename, or move code.
---

# Refactor

**Behaviour-preserving only.** If what an endpoint returns, what a component renders, or
when a job fires changes, it is a feature — plan and test it as one. Large or cross-cutting
structural work goes to `figure-it-out`.

## Discipline

1. The existing suite passes **before** you start. If it doesn't, that is the task. If the
   area has no coverage, pin it first with a characterization test or an equivalence
   harness. Typecheck and lint are not a pin.
2. Name the target shape: the module layout, types, and call graph you would build today.
   The reshape must delete branches or invalid states, not add indirection.
3. Refactor.
4. The same tests, unchanged, still pass. Paste the run. For a larger reshape, also run an
   equivalence check: a script that diffs old against new output, or a recorded baseline
   replayed against the new code.

If you had to edit a test to make it green, behaviour changed. Stop and say so.

## Sequencing

One refactor per commit, separate from feature work. A diff that both moves code and changes
it cannot be reviewed.

Subtract before you add: delete dead code, one-caller wrappers, and redundant validators
first. Then small moves in order: rename → extract → move → delete. Each independently green.
For an API reshape, migrate every caller and delete the old API in the same wave, with no
shim. Spot-check every rename against the files; renames miss usages in strings and prose.

## Deliberate boundaries are not gaps

Every stack has architectural choices that look like something to "improve" — a missing
layer, a function that could be a class, a duplicate that could be abstracted. If your router
links a stack `refactor.md`, it lists them. Read it first; if one genuinely blocks you, raise
it rather than routing around it.

## Not a refactor

Anything that changes persisted shape (a column, a route path, a query key, a public
signature other code imports) is a behaviour change with a migration or a compatibility
story. Confirm before writing that.

## Keep it only if it helps

The measure is reader load: fewer layers between a question and its answer, less hidden
state. If the diff lowers reader load nowhere, revert it.

## Report

The structure that changed, the pin you held it against, the equivalence proof, the
reader-load change, and what shipped versus what you reverted.
