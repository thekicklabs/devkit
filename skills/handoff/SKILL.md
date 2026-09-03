---
name: handoff
description: Write HANDOFF.md so the next agent or person can resume without re-deriving anything — goal, what is done with evidence, what is not, decisions and why, open questions, exact commands. Use when stopping mid-task, when context is running out, or when asked to hand over.
---

# Handoff

Write `HANDOFF.md` at the repo root (or update it). Be specific enough that someone with no
memory of this session can continue in five minutes. Facts, not narrative.

```markdown
# Handoff — <task in one line>

## Goal
What was asked, restated. Link the plan if one exists.

## Done — with evidence
- <thing> — proved by `<command>` → <one line of its real output>
- …

## Not done
- <thing> — why it stopped (blocked / out of time / needs a decision)

## Decisions taken, and why
- <decision> — <reason>; alternatives considered: <…>

## Open questions
- <question> — who can answer, what changes depending on the answer

## Resume
```bash
<exact commands to get back to the working state: branch, install, run tests>
```

## Files touched
<path> — <what changed, one line each>
```

Rules:

- Evidence is real output, pasted. "Tests pass" is a claim.
- List what you were *about* to do next, in order.
- If a rule file under `AGENTS/` should change because of what you learned, say which and
  what — do not leave it in your head.
- Do not commit `HANDOFF.md` unless asked; it is a working note.
