---
name: kick-mode
description: Route non-trivial work to the right kick skill or playbook, run subagents within a budget, and verify before reporting done. Use for /kick-mode, multi-file changes, design choices, bugs with an unknown cause, performance work, PRs to drive or land, and long or unattended runs.
---

# kick-mode

## Platform

These skills use Claude Code tool names: the `Skill` tool, the `Agent` tool, `AskUserQuestion`. On Codex, read [`references/codex-tools.md`](references/codex-tools.md) for the equivalents.

Track the playbook in the session's task tool (`TaskCreate`/`TodoWrite` on Claude Code, `update_plan` on Codex). With no task tool, keep an uncommitted `todo.md` checklist in the work directory.

## Precedence

1. The user's rules: the instructions file (`CLAUDE.md`, `AGENTS.md`) and the workflow rules it routes to, especially the ask/decide table and the definition of done.
2. This skill and the playbooks it routes to.
3. The principles.

When a principle or playbook step conflicts with the user's rules, the rules win. Say which rule decided it.

If no workflow rules are installed, ask before: a new dependency, a contract change that breaks the other side, anything touching auth, payments or personal data, deleting or overwriting existing work, migration or backward-compatibility code, and a departure from the project's own conventions. Decide everything else, and say which reading you took.

## Enter when, skip when

Enter kick-mode when the task:

- touches more than one file, or changes a signature other files call;
- involves a design or architecture choice;
- is a bug whose cause is not yet known, or a performance issue;
- drives or lands a PR;
- runs long or unattended.

Skip it for a contained one-file change with an obvious test, a question one read answers, a one-line edit, or a prose fix. Work directly, and still verify on the real artifact.

## Route

Match the intent, then open the skill or playbook. For a playbook, copy its steps into the task list verbatim before any task-specific items. A step you skip stays in the list as `skip: <reason>`.

| Intent | Go to |
| --- | --- |
| Anything non-trivial, or a request that reads two ways | `plan` |
| Read-only question: how does X work, why is Y built this way, should we do X or Y | [Investigation](playbooks/investigation.md) |
| How code works, where something should live | `how` |
| Why code is this way, regression history | `why` |
| A reported defect | [Bug fix](playbooks/bug-fix.md) |
| A measured slowness | [Perf issue](playbooks/perf-issue.md) |
| Sustained improvement of one metric | [Hillclimb](playbooks/hillclimb.md) |
| New or changed behaviour | [Feature](playbooks/feature.md) |
| Behaviour-preserving restructure | [Refactoring](playbooks/refactoring.md) |
| Building test-first | `tdd` |
| Types, signatures and module shape before code | `architect` |
| A throwaway sketch to settle a design or empirical fork | [Prototype](playbooks/prototype.md) |
| What a change could break beyond its diff | `blast-radius` |
| Large or cross-cutting work, or nothing above fits | `figure-it-out` |
| Reviewing your own diff | `code-review` |
| Adversarial review across agents | `interrogate` |
| Before committing | `deslop`, then `commit` |
| Before review | `no-comments` |
| Opening a PR | [Opening a PR](playbooks/opening-a-pr.md) |
| PR status, "get it green", review comments | `babysit` |
| Failing checks | `fix-ci` |
| Merge conflicts | `fix-merge-conflicts` |
| Landing a verified PR or stack | [Shipping](playbooks/shipping.md) |
| A long run to a predicate without stopping | [Autonomous run](playbooks/autonomous-run.md) |
| Writing or editing a skill | [Authoring a skill](playbooks/authoring-a-skill.md) |
| Stopping mid-task | `handoff` |
| Resuming earlier work | `recall` |
| Docs, PR text, commit bodies | `technical-writing`, then `unslop` |
| Explaining work plainly | `bro`, `teach` |
| A reviewable decision trail | `show-me-your-work` |
| A scripted way to drive the app | `create-verification-skill`, `maintain-verification-skill` |
| A harsh maintainability audit | `thermo-nuclear-code-quality-review` |
| Tidying a PR for reviewers | `make-pr-easy-to-review` |
| Parallel coverage, races, gauntlets (on request) | `swarm` |
| Competing implementations of one artifact (on request) | `arena` |

## Principles

Read a principle's file in full before you apply or cite it. Each entry names when it applies.

**Core**

- [**Laziness Protocol**](principles/laziness-protocol.md). Refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading. Bias to deletion and the smallest change that solves the problem.
- [**Foundational Thinking**](principles/foundational-thinking.md). Before writing logic: core types and data structures, scaffold-vs-feature sequencing, what concurrent actors share.
- [**Redesign from First Principles**](principles/redesign-from-first-principles.md). Integrating a new requirement into an existing design. Redesign as if it had been foundational from day one.
- [**Attack the Premise**](principles/attack-the-premise.md). Repeated fixes share an assumption and fail. State that assumption and choose an observation that can challenge it before another fix depends on it. Count work per actor when the hypothesis concerns uneven assignment.
- [**Subtract Before You Add**](principles/subtract-before-you-add.md). Sequencing an addition, refactor, or rewrite. Remove dead weight first, then build on the simpler base.
- [**Minimize Reader Load**](principles/minimize-reader-load.md). Reviewing or shaping code that's hard to trace. Count layers and hidden state, collapse one-caller wrappers, shrink mutable scope.
- [**Outcome-Oriented Execution**](principles/outcome-oriented-execution.md). Planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture, don't preserve throwaway compatibility states.
- [**Experience First**](principles/experience-first.md). Product, UX, or feature-scope tradeoffs. Choose user delight over implementation convenience.
- [**Exhaust the Design Space**](principles/exhaust-the-design-space.md). A novel interaction or architectural decision with no precedent. Build 2-3 competing prototypes and compare before committing.
- [**Build the Lever**](principles/build-the-lever.md). Any non-trivial work. Build the tool that does or proves it (codemod, script, generator), not by hand. The tool is the artifact a reviewer reruns.

**Architecture**

- [**Model the Domain**](principles/model-the-domain.md). Writing stateful logic, or code that branches a lot or repeats a shape assumption across files. Encode the domain in a structure (state machine, typed model, table or registry, reducer, boundary, the right collection) instead of scattered conditionals.
- [**Boundary Discipline**](principles/boundary-discipline.md). Wiring validation, error handling, or framework adapters. Guards at system boundaries, trust internal types, keep business logic pure.
- [**Type System Discipline**](principles/type-system-discipline.md). Designing types or a signature in any typed language. Make illegal states unrepresentable, brand primitives, parse external data at boundaries.
- [**Make Operations Idempotent**](principles/make-operations-idempotent.md). Designing commands, lifecycle steps, or loops that run amid crashes and retries. Converge to the same end state.
- [**Migrate Callers Then Delete Legacy APIs**](principles/migrate-callers-then-delete-legacy-apis.md). Introducing a new internal API while old callers exist. Migrate and delete in one wave.
- [**Separate Before Serializing Shared State**](principles/separate-before-serializing-shared-state.md). Concurrent actors might write the same file, branch, key, or object. Eliminate the sharing first.

**Verification**

- [**Prove It Works**](principles/prove-it-works.md). After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- [**Fix Root Causes**](principles/fix-root-causes.md). Debugging. Trace each symptom to its root cause, reproduce first, ask why until you reach it.
- [**Sequence Work into Verifiable Units**](principles/sequence-verifiable-units.md). Multi-step work (sweeps, migrations, runs of similar edits) and how you stack commits and PRs. Break work into small units that each end in a check, verify each before the next, and order delivery so the sequence proves itself.
- [**Test Behavior, Not Implementation**](principles/test-behavior-not-implementation.md). Writing, changing, or keeping a test. Identify a relevant defect and check that the complete test arrangement detects it. Assert the required result or effect, including absence and fixed values when the contract requires them.
- [**Explain the Number**](principles/explain-the-number.md). Before you trust, report, or act on a number you measured (a speedup, a regression, a throughput, a latency, or an eval result). Find what limits it, and rule out that it measured something other than the work you think.

**Delegation**

- [**Guard the Context Window**](principles/guard-the-context-window.md). Context fills up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents, keep summaries in the main thread.
- [**Never Block on the Human**](principles/never-block-on-the-human.md). Tempted to ask "should I do X?" on reversible work. Proceed, present the result, let the human course-correct.

**Meta**

- [**Encode Lessons in Structure**](principles/encode-lessons-in-structure.md). You catch yourself writing the same instruction a second time. Encode it as a lint, metadata flag, runtime check, or script instead of more text.

## Subagents

Spawn playbook delegates with `subagent_type: "kick:worker"`. Skills that set their own `subagent_type` keep it.

- **Roles.** Skills name a role (`default`, `strong`, `fast`, `panel`, `reviewer`), never a model. Resolve it per [models](references/models.md): the user's config first, then the defaults there.
- **Fan-out.** At most `fan-out` subagents (3 by default) run at once. Queue the rest.
- **Read-only guard.** Before a read-only role runs (a reviewer, explorer, or investigator), note `git rev-parse HEAD` and `git status --porcelain`. Compare after it returns. A difference means the run was tainted: discard its output and say so.
- Run subagents in the background, and pass file pointers, not file contents.
- You own every subagent's work. Read the diff it returns and write your own summary.
- Give new work to a fresh subagent with the consolidated brief: the original ask, every later directive, and the prior agent's report and branch. Resume an existing agent only when the work needs state that lives in it, such as its uncommitted changes or a process it runs.
- Stop an abandoned agent and confirm it stopped. `git status` contradicting an agent's claim about the tree means it is still running.
- Give every file-writing delegate its own worktree or branch.

## Autonomy

Interactive by default: the ask/decide rules in [Precedence](#precedence) decide when to stop and ask. Hands-off work happens only inside the [Autonomous run](playbooks/autonomous-run.md) playbook, which the user starts explicitly.

No is an acceptable answer. Asked whether to do something, or shown an approach, give your real judgment. Decline or push back when that is true.

## Done

The definition of done in the user's workflow rules applies. Without one: the suite green with its output pasted, lint and typecheck clean, the change seen working where it runs, and no leftovers. A non-trivial diff also needs a clean `interrogate` before you report it done.

**Driver.** To see a change working, use the project's verification skill when it has one (`create-verification-skill` makes one). Otherwise use `run` on Claude Code, or run the app yourself and read its real output. "Inconclusive" or the wrong surface is not a pass.

## Reply

Apply `unslop` while you draft.

- Lead with the evidence: what you ran and what it showed.
- Short declarative sentences, one thought each.
- Every claim carries its evidence or a label in the same sentence: measured, inferred, or guess.
- Link only artifacts you produced or read this session.
- Never hand the human a check you could run.

Each playbook ends with a **Reply** line naming what that reply must contain.
