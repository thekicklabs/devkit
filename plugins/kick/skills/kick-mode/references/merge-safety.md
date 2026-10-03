# Merge and restack safety

Use this with [Shipping](../playbooks/shipping.md). These operations add revision and destination checks; they do not grant merge authority.

## Cancel pending merges

A PR can carry two future merges: auto-merge and a merge-queue entry. Read both before any rewrite or retarget.

```sh
gh pr view "$pr" --json headRefOid,baseRefName,autoMergeRequest,mergeStateStatus,state
gh pr merge "$pr" --disable-auto
```

If the PR sits in a merge queue, dequeue it with the GraphQL `dequeuePullRequest` mutation. Read the PR again and proceed only when both mechanisms are absent on the same head. A missing field or an API error never means "absent". Cancellation is an observation, not a lock: if state changes, stop and reconcile.

## Preserve concurrent writes and child changes

Capture the remote branch SHA before rewriting with `git ls-remote --exit-code origin "refs/heads/$branch"`, and check that exactly the intended ref came back. Keep that SHA in the operation record. An implicit lease or an earlier read is not enough; a background fetch can move a tracking ref.

After confirming the parent squash landed in the intended destination, fetch trunk and find the recorded old parent tip the child was built on. Verify it is an ancestor of the child and inspect `old-parent..child` to confirm the range holds only child work. If it does not, reconstruct the boundary before going on. Never infer it from the parent's new squash commit.

```sh
git merge-base --is-ancestor "$old_parent_tip" "$child"
git rebase --onto "$trunk_tip" "$old_parent_tip" "$child"
git push --force-with-lease="refs/heads/$child:$captured_remote_head" \
  origin "HEAD:refs/heads/$child"
```

Run the rebase in the child's clean worktree. Inspect the resulting diff, reassess whether the review still applies, and run the checks at the new head. If the lease refuses the push, fetch and reconcile the concurrent work; never refresh the lease and retry blindly. Retarget only after cancellation is verified.

## What the service guards

GitHub's merge head condition is `--match-head-commit` in `gh`, `expectedHeadOid` in GraphQL `mergePullRequest`, or `sha` in the REST merge endpoint. None of them guards the base branch. Observe the base just before and after, and do not call those observations atomic.

A queue or auto-merge request can outlive the revision it was armed on. Use one only when repository rules enforce the required verification on the eventual revision. A prose verdict or a green check on an older head is not such a gate. If the repository requires a queue and the gate is missing, stop rather than bypass protection.

After a merge, confirm state `MERGED`, the approved final head, the intended base, and a non-null merge commit. Fetch the destination and run `git merge-base --is-ancestor "$merge_commit" "$destination_tip"` before advancing.

References: [gh pr merge](https://cli.github.com/manual/gh_pr_merge), [GraphQL pull request mutations](https://docs.github.com/en/graphql/reference/pulls), [REST merge endpoint](https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request).
