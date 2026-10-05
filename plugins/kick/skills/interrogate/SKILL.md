---
name: interrogate
description: "Adversarial review of a diff by several agents at once: an in-process reviewer plus headless Claude Code and Codex CLIs, all read-only, with you as the judge. Use for \"interrogate\", \"adversarial review\", \"multi-model review\", \"challenge this\", \"stress test this code\", \"tear this apart\", or before reporting a non-trivial diff done."
---

# Interrogate

On Codex, read the [platform mapping](../kick-mode/references/codex-tools.md) before following this skill.

Reviewers from different vendors review the same diff against the same brief, in parallel and read-only. You are the judge: dedupe, try to disprove, bucket. The deliverable is a verdict. Nothing changes here; fixes happen only inside an [Autonomous run](../kick-mode/playbooks/autonomous-run.md).

The diff, and any file a reviewer opens, goes to that reviewer's vendor. Claude reviewers are denied `.env` files, and the brief tells every reviewer not to open secrets; Codex's read-only sandbox can still read them.

`scripts/` below means this skill's `scripts/` directory under the installed plugin.

## 1. Scope

Pick the diff from the request: uncommitted changes (`--uncommitted`), the branch against its base (`--base <ref>`), or a PR (`--pr <number>`). When the request does not say, use the uncommitted changes if there are any, otherwise the branch against its base.

## 2. Intent

Write one paragraph: what the change is for, from the user's words, the commits, and the PR body. If you are unsure, ask. Inside an autonomous run, log your reading instead.

## 3. Prepare

```bash
scripts/review.sh prepare --uncommitted <<'EOF'
<the intent paragraph>
EOF
```

It prints the run directory, `$(git rev-parse --git-dir)/kick/<timestamp>/`, and stops if the diff is empty. The directory holds `diff.patch`, `intent.md`, `schema.json`, `prompt.md`, and `state`. The brief in `prompt.md` takes its dimensions, disprove step, and severity and confidence scales from the `code-review` skill, plus the project's `AGENTS.md` or `CLAUDE.md` and any `AGENTS/*/review.md`; reviewers run without the user's instructions files. `state` snapshots HEAD, `git status`, and the working-tree content.

## 4. Roster

`grep '^reviewers:'` the config from [models](../kick-mode/references/models.md). Entries are `self` (an in-process `kick:reviewer`) and CLI names.

If the line is missing, run `scripts/detect-reviewers.sh`, propose `self` plus every installed, authed, `stable` CLI, and ask (`AskUserQuestion` on Claude Code, plain text on Codex). Save the answer as a `reviewers:` line in the config; `setup-kick` owns the rest of the file.

Skip the CLI of the runtime you are running in (`claude` on Claude Code, `codex` on Codex): `self` covers that vendor more cheaply. `agent`, `gemini`, and `opencode` are experimental; their commands are unverified, so say so when one runs.

State the roster in one line before dispatch, such as `Reviewers: self (opus), codex (gpt-6.1-sol @high)`.

## 5. Dispatch in one turn

- **self.** Spawn `subagent_type: "kick:reviewer"` on the `reviewer` role's model with the brief "Follow `<run>/prompt.md` and return only the JSON object it asks for."
- **Each CLI.** Run `scripts/review.sh run <cli> <run>` in the background. On Claude Code use the Bash tool's `run_in_background`, because a foreground command stops at 10 minutes. `KICK_REVIEW_TIMEOUT` bounds each run (900 seconds by default). The reviewer's model comes from the config's `<cli> reviewer:` line; the effort is always `high`.

## 6. Collect

Each CLI run writes `<run>/<cli>.status`:

| Status | Meaning |
| --- | --- |
| `ok` | finished; parse its output |
| `timeout` | hit the limit |
| `failed` | exited non-zero; read `<cli>.err` |
| `tainted` | HEAD, `git status`, or file content changed during the run; discard its findings and show the user `git status` |

Parse the output yourself. Claude Code prints a JSON envelope with the findings object in `structured_output`. Codex writes the object to `codex.json`. For `self`, apply kick-mode's read-only guard.

Report every failure and what it cost, such as "Codex timed out, so this review covers one vendor."

## 7. Judge

You are the lead reviewer, not an aggregator. Read [`references/lead-judgment.md`](references/lead-judgment.md).

1. Dedupe by root cause, and note which reviewers raised each.
2. Build the agreement map. A root cause two or more reviewers found independently is high signal.
3. Try to disprove each finding against the code, per step 3 of `code-review`. Never accept a finding on a reviewer's word.
4. Bucket each survivor as **Act on**, **Consider**, **Noted**, or **Dismissed**, with a one-line reason.

## 8. Report

- **Intent.** The paragraph from step 2.
- **Roster.** Each reviewer, its model, its status, and its finding count.
- **Act on**, **Consider**, **Noted**, **Dismissed.** Each finding with its location, which reviewers raised it, and your reason.
- **Agreement map.** Where reviewers converged and diverged, and what that says.
- **Run directory.** The path, so the raw outputs can be read.

Inside an autonomous run, fix the Act-on findings, rerun the suite, and interrogate again, for at most two rounds. Log whatever remains.
