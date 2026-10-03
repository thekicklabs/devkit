---
name: commit
description: Make a commit that a reviewer can trust — conventional subject, one logical change, suite run and pasted, convention file updated in the same commit. Use whenever committing or asked to commit.
---

# Commit

Commit or push **only when asked**. Never commit to `main` directly — branch off it:
`feat/<slug>`, `fix/<slug>`, `chore/<slug>`.

## Before

1. Run the suite for what changed. Paste the output. A failing suite means no commit —
   report the failure instead.
2. `git status` and `git diff` — read the whole diff. Remove leftover debug output,
   commented-out code, and comments that describe something no longer there.
3. If a convention changed, its rule file under `AGENTS/` changes in this commit. A rule
   that lives only in a diff is a rule the next agent will break.

## Shape

- **One logical change per commit.** A model change and its migration are one change; a
  refactor and a feature are two commits.
- **Subject**: `type(scope): imperative summary`, ≤72 chars. Types: `feat` `fix` `chore`
  `refactor` `test` `docs`. No trailing period.
- **Body** only when the subject cannot carry the *why*. Never narrate the diff.
- **No AI co-author trailer.** No `Co-Authored-By: Claude/Codex/Cursor`.

## Do

```bash
git add <specific paths>      # never `git add -A` blind
git commit -m "feat(api): add cursor pagination to applications list"
```

Stage by path so an unrelated file does not ride along. Do not amend or force-push
something already pushed unless asked.
