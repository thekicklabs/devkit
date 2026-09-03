# Workflow — applies to every task

**Read when:** always, before anything else.
**Then:** route on to the stack files linked from `AGENTS.md`, and `project.md` when there is one.

---

## Before you write code

1. Read the routed files. A convention you invent is a convention someone has to undo.
2. Look for the existing thing first — a helper, a service function, a component. Reuse
   beats reimplementation.
3. If two readings of the request produce materially different work, ask. If one reading is
   obviously right, take it and say which you took. The `plan` skill is the long form.

## Branches and commits

The `commit` skill owns this: branch off `main`, conventional subjects, one logical change,
commit or push only when asked.

## What "done" means

Never report done on a partial. If part of the scope is blocked, finish everything else and
say plainly what you left and why.

| Check | Done means |
| --- | --- |
| Lint / format / typecheck | clean, using the stack's commands |
| Tests | the relevant suite green — output pasted, not described |
| Seen working | the change exercised where it runs: the dev server, the CLI, the job |
| Leftovers | no debug output, no commented-out code, no stale comments |
| Schema | any persisted-shape change ships with its migration in the same commit |

Each stack's `AGENTS.md` names the exact commands. Run them where the dependencies live —
inside the container when the stack is compose-first.

Paste real command output. "Tests pass" without the run is a claim, not a result.

## When to ask vs. decide

**Decide yourself:** naming, file placement inside an established structure, which existing
helper to reuse, obvious edge-case handling, test case selection.

**Ask:** a new dependency · a schema/API contract change that breaks the other side ·
anything touching auth, payments, or personal data · deleting or overwriting existing work ·
migration or backward-compatibility code (it is often for a feature nothing uses) · a
departure from a rule in these files.

## Changing a convention

Rules live in exactly one file. To change one:

1. Edit the pattern file that owns it — not the feature you happened to be writing.
2. If the routing changes, update the table that points at it.
3. Same commit as the code change.

Never inline a rule into a feature file "for visibility". Two copies diverge; the router
stops being trustworthy; agents start guessing again.

## Comments

Default to none. A comment earns its place only when the code cannot say it: a non-obvious
constraint, a workaround with its reason, a link to the decision. No docstring that repeats
the signature; no comment that narrates the diff; none that refers to something removed.
