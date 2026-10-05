### Opening a PR

Invoked at the end of every other playbook that changes code.

**Branch.** Work on a branch off main, in a worktree when subagents share the checkout. A delegate gets its own worktree or branch. A dirty branch with unrelated work: move the patch to a fresh worktree. Before you commit or push from a worktree, stop every agent that still holds it, confirm each stop, then run `git status` and read the tree you are about to ship.

**Commits.** Commit through the `commit` skill. Rebase into small, ordered commits before opening the PR, each one landable and in an order that tells the story. Amend when the fix belongs in the commit you just made; add a new commit when it is separable.

**Before review.** Run `deslop` over the diff before committing and `no-comments` before review. Write the title, description, and commit bodies with `technical-writing`, then apply `unslop`.

**Title.** Conventional Commits: `type(scope): subject`, imperative, no trailing period. The scope is the changed area. Name a real symbol when one carries the change.

**Description.** A briefing, not a lab notebook. A reviewer with the diff should learn in under a minute why the change exists, what it leaves out, what it could break, and how you proved it works. The squash commit body is the PR body, so keep it under about 40 lines. Use `##` headings in this order and drop any with nothing to say:

- `## Why`: the problem and the approach in one to three sentences.
- `## What changed`: one to three bullets. Name both sides of a rename.
- `## Scope`: what the PR covers and what it deliberately leaves out.
- `## Tradeoffs`: only rejected alternatives a reviewer would ask about.
- `## Blast Radius`: who or what the change touches, and why that is safe or risky.
- `## Verification`: one to three bullets, each a real run and its outcome. For a performance change, one primary number as `before → after` with its unit.

Attach screenshots or video when they prove a claim. Put long evidence in a linked artifact, not the body.

**Forge.** Use `gh`. Open the PR ready, never as a draft: `gh pr create --base <base>`, then `gh pr view <number>` before you describe its status.

**Stacks.** Prefer several narrow PRs to one large one. A stack is a base-branch chain: the root targets trunk, and each child rebases onto its parent's exact tip and targets the parent branch (`gh pr create --base <parent-branch>`, or `gh pr edit <pr> --base <parent-branch>` to retarget). Branch from trunk only for independent work.

**After opening.** Post the URL and keep building. Opening a PR does not start a babysit; run `babysit` only when the user asks, once the stack exists. A subagent that opens a PR posts the URL and returns to its parent, which decides on review.
