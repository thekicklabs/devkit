### Shipping

Verify on the real surface per kick-mode's [Driver](../SKILL.md#done).

**You own what lands.** Land one verified PR at a time and confirm it landed before advancing. This is the half after `babysit`, and it needs the user's explicit request to merge, land, or ship.

1. **Capture the chain.** List the affected PRs bottom-to-top: head branch and SHA, base branch and SHA, and the destination. Leave unrelated PRs alone. Read [Merge and restack safety](../references/merge-safety.md) before merging, arming, rebasing, or retargeting.
2. **Verify each PR independently.** A fresh `kick:worker` per PR, in its own worktree, exercises the real surface on base versus head and returns `PASS`, `PASS+NOTES`, or `FAIL`. The verifier must not have written the code. Green CI and a bot approval do not replace this verdict. Record the head SHA, base SHA, base branch, and `git patch-id` of the base-to-head diff.
3. **Find the contiguous verified run.** Walk up from the lowest unmerged PR and stop at the first without `PASS` or `PASS+NOTES`. Report that ceiling. A verified child above an unverified parent cannot land yet.
4. **Cancel pending merges before changing the chain.** Cancel auto-merge and queue entries on every PR a rewrite or retarget can affect, per the safety reference, and read back that both are gone. If cancellation fails or a PR merges meanwhile, stop and reconcile.
5. **Prepare only the bottom PR.** Fetch trunk. After a parent squash, replay only the child's own commits. Push with an explicit lease against the remote SHA you captured. Retarget only this PR.
6. **Reassess.** A changed head or base invalidates the verdict unless the patch-id matches and the destination is unchanged. Rerun the checks after any rewrite or retarget.
7. **Merge with a head condition.** `gh pr merge <pr> --squash --match-head-commit <verified-head>`. Never `--admin`. Use auto-merge or a merge queue only when repository rules enforce the verification on the revision that lands; otherwise stop at merge-ready and say why.
8. **Confirm the landing.** Read the PR's state, final head, base, and merge commit, fetch the destination, and run `git merge-base --is-ancestor <merge-commit> origin/<base>`. A queued response is not a merge. Then repeat from step 4 for the next PR.
9. **Stop at the ceiling.** Report what landed and what the next PR needs. Extending the run is a new pass through step 2.

**Reply:** the verified run and its ceiling, each verdict with its head and base, the cancelled requests, the confirmed landings, and anything unresolved.
