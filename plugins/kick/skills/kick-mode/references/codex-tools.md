# Codex mapping

kick skills use Claude Code tool names. On Codex the files are the same and only the names resolve differently.

## Tools

| Claude Code | Codex |
| --- | --- |
| Read, Grep, Glob | `shell` (`cat`, `rg`, `find`) |
| Edit, Write | `apply_patch` |
| Bash | `shell` |
| WebFetch | `shell` with `curl` |
| WebSearch | `web_search` |
| The `Skill` tool, `/kick:<name>` | Skills load natively; mention one as `$kick:<name>` |
| The `Agent` tool | `spawn_agent` |
| N subagents in one turn | N `spawn_agent` calls in one response |
| Waiting on a subagent | `wait_agent`, then `close_agent` |
| `TaskCreate`, `TodoWrite` | `update_plan` |
| `AskUserQuestion` | Ask in plain text. Codex has no structured-choice tool. |

Subagents need `[features] multi_agent = true` in `~/.codex/config.toml`. Without it, run the fan-out steps one at a time yourself.

## Subagents

Roles resolve per [models](models.md), whose Codex column applies here.

Codex plugins ship no agent types. Where a skill names `subagent_type: "kick:<role>"`, call `spawn_agent` with instructions that begin "Read `<plugin root>/agents/<role>.md` in full and follow it", where the plugin root is two directories above the skill's `SKILL.md`. Pass the task brief after that line. For `kick:reviewer`, also pass `reasoning_effort: "high"`.

`spawn_agent` already runs beside your turn, so there is no background flag. Read-only cannot be enforced on a Codex subagent; snapshot `git status` and `HEAD` before a review and compare after it.

## Built-in skills named in kick

| Named | On Codex |
| --- | --- |
| `run` (drive a CLI, TUI or server to see a change work) | Run it yourself with `shell` and read the real output. |
| A project UI driver | Use the automation you have, or give the user a concrete manual check. Never claim done without observing the artifact. |
| `loop` (self-paced re-checks) | Codex has no `loop`. Re-run the check yourself on a cadence. |

## Instructions file

Where a skill says "your instructions file", Codex reads `AGENTS.md` (the project root, plus `~/.codex/AGENTS.md`). Claude Code reads `CLAUDE.md`.

## Session hook

Codex runs kick's SessionStart hook only after you trust it in `/hooks`. Until then, invoke `$kick:kick-mode` yourself.
