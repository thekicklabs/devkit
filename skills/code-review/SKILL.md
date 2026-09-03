---
name: code-review
description: Review a diff for what blocks, what should be fixed, and what is worth asking about — then hand off to the stack's own review checklist. Use when asked to review changes, a PR, or a branch.
---

# Code review

Read the whole diff before commenting on any of it. Then work down these lists, and finish
with the stack's `review.md` under `AGENTS/<stack>/`, which holds the stack-specific rows.

Report findings ranked, most severe first, each with file:line and a concrete failure case.
No finding without a way it actually goes wrong.

## Blocking

- [ ] Tests not run, or run and failing, or "passes" claimed without output.
- [ ] New behaviour without a test; a bug fix without a regression test.
- [ ] Scope larger than the request — unrelated changes riding along.
- [ ] A convention changed in code but not in its `AGENTS/` file.
- [ ] Security: input trusted from the client, authorisation missing on a path, a secret in
      code or config, personal data in a log line or error message.
- [ ] A new dependency nobody agreed to.
- [ ] Data-shape change without its migration / contract update on the other side.

## Should fix

- [ ] Comments that restate the code, or refer to something the diff removed.
- [ ] Leftover debug output, commented-out code, TODOs with no owner.
- [ ] `any` / `Any` where a real type exists; a suppressed type error with no explanation.
- [ ] Error swallowed silently, or a broad catch that hides the real failure.
- [ ] Duplicated logic where an existing helper does the job.
- [ ] A name that lies about what the thing does.

## Worth asking about

- [ ] An abstraction introduced for one caller.
- [ ] Backward-compatibility shims for a feature nothing uses.
- [ ] A behaviour change hiding inside a "refactor" commit.

## Then

Open `AGENTS/<stack>/review.md` for each stack the diff touches and run its checklist.
