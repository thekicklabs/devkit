# Models and roles

Skills name a role, never a model. Resolve a role in this order:

1. The user's config, `${XDG_CONFIG_HOME:-~/.config}/kick/config.md`. Read it with `cat` when a skill needs a role. A line `<runtime> <role>: <value>` sets one role, as in `claude strong: opus` or `codex fast: gpt-6-luna`.
2. The defaults below.

| Role | Used for | Claude Code | Codex |
| --- | --- | --- | --- |
| `default` | playbook delegates, and anything a skill does not assign | `inherit` | `inherit` |
| `strong` | bug fixes, perf work, hillclimbs, the hardest judgment calls | `opus` | `gpt-6.1-sol` |
| `fast` | explorers, investigators, transcript mining, mechanical edits, swarm workers | `sonnet` | `gpt-6-luna` |
| `panel` | arena and architect runners, one runner per entry | `opus, sonnet` | `gpt-6.1-sol, gpt-6-luna` |
| `reviewer` | interrogate's reviewers, in-process and external | `opus` at `high` | `gpt-6.1-sol` at `high` |

`fan-out: 3`. At most this many subagents run at once. A skill that needs more queues the rest.

## Semantics

- `inherit` runs the role on the session's model: omit `model` on the `Agent` call, or leave it off `spawn_agent`.
- Effort is not a role setting. Workers inherit the session's effort. Reviewers run at `high`: the `kick:reviewer` agent sets it on Claude Code, Codex takes `reasoning_effort: "high"` on `spawn_agent`, and `interrogate` passes it to external CLIs explicitly because a user's CLI config can default higher.
- If the runtime rejects a configured model, run the role on `inherit` and say so in the reply.
- If Codex's `spawn_agent` accepts no model, run `fast` roles on the session model at `reasoning_effort: "low"` and `strong` roles at `"high"`.
- A heavier or newer model is an opt-in: write it into the config. The defaults stay within an everyday subscription.

## Config keys

One `key: value` per line, so scripts can `grep` them.

| Key | Example | Read by |
| --- | --- | --- |
| `claude <role>` | `claude fast: sonnet` | every skill that spawns |
| `codex <role>` | `codex strong: gpt-6.1-sol` | every skill that spawns |
| `fan-out` | `fan-out: 3` | kick-mode, arena, swarm, how, why |
| `reviewers` | `reviewers: codex, self` | interrogate |
| `session hook` | `session hook: off` | the SessionStart hook |
