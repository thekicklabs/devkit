---
name: arena
description: "Run parallel candidates at the same task, pick a base, and graft the strongest parts of the others into it. Opt-in: use for /arena, 'arena this', 'throw it in the arena', or when the user accepts an offered bakeoff on a hard-to-reverse shape."
---

# Arena

On Codex, read the [platform mapping](../kick-mode/references/codex-tools.md) before following this skill.

Run parallel attempts at the same task. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the result.

Arena is opt-in. Run it when the user asks, or accepts an offer, because each runner costs a full attempt.

## Start

Open a todolist with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Pick
4. Graft
5. Verify

## Phase A: Frame

The candidates receive the same prompt, so the prompt is the contract.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. The rubric is your tool in Phase C. Candidates only see the task.
3. Pick the runners: one per entry of the `panel` role in [models](../kick-mode/references/models.md), two by default. Run the same model twice when the work is generation-bound rather than judgment-sensitive. Never run more than `fan-out` at once.
4. Assign output paths. Each candidate writes to its own location (a git worktree where possible, otherwise `/tmp/arena-<slug>/candidate-<n>/`), per the [separate-before-serializing-shared-state](../kick-mode/principles/separate-before-serializing-shared-state.md) principle.

## Phase B: Fan out

Spawn the runners in one message, in the background, each with the task, the path to the shared grounding, its own output path, and instructions to produce both the artifact and a short rationale.

Each rationale names the alternatives the candidate considered and what it rejected.

If a candidate fails to produce output, proceed without it and note the dropout in the synthesis record.

## Phase C: Pick a base

You are the judge. Read every candidate end to end before picking.

Score each candidate against the rubric criterion by criterion, not on holistic feel. When two candidates score close, read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. Prefer the cleaner boundary or smaller API when two feel tied, per the [laziness-protocol](../kick-mode/principles/laziness-protocol.md) principle.

Record the pick and the reason in a short synthesis note alongside the base artifact.

## Phase D: Graft

Walk each other candidate once more and identify what is worth porting into the base. The signal is usually one or two things per candidate, not most of it.

Fold each graft in by hand, per the [redesign-from-first-principles](../kick-mode/principles/redesign-from-first-principles.md) principle. Don't paste mechanically. The result has to remain coherent under one mental model.

Record what was grafted, from which candidate, and what was rejected and why.

When the candidates converge on the same shape, that is a strong agreement signal. Note the convergence and ship the consensus shape. When they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase E: Verify

The synthesized artifact has to hold up under the same scrutiny as any other output, per the [prove-it-works](../kick-mode/principles/prove-it-works.md) principle.

If verification surfaces a problem the arena did not catch, either Phase A was wrong (reframe and re-run) or one candidate caught it and you missed the graft (go back to Phase D). Don't paper over.

## Outputs

One synthesized artifact. One short synthesis note alongside, naming the base, the grafts with their source candidate, the rejections, any dropouts, and the verification result.
