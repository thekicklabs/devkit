# devkit

One repo that sets up a machine and every coding agent on it the same way: shared skills,
one set of working rules, per-stack conventions — copied into the right place for Claude
Code, Codex and Cursor — plus the bootstrap scripts for a fresh Debian/Ubuntu VM.

The repo is also a plugin marketplace, `kicklabs`, for Claude Code and Codex. Its `kick`
plugin carries the skills, agents and session hook; devkit carries the rules, stacks and
router the plugin cannot install.

## The kick plugin

```bash
# Claude Code
claude plugin marketplace add thekicklabs/devkit
claude plugin install kick@kicklabs

# Codex
codex plugin marketplace add thekicklabs/devkit
codex plugin add kick@kicklabs        # then trust its hook in /hooks
```

Then run `/kick:setup-kick` (Claude Code) or `$kick:setup-kick` (Codex) once: it picks the
model for each role, the agent CLIs `interrogate` uses as reviewers, the fan-out cap, and
whether the session hook runs, and writes them to `~/.config/kick/config.md`.

- **`kick-mode`** routes non-trivial work to a skill or playbook. The SessionStart hook
  points every session at it; `session hook: off` in the config or `KICK_HOOK=off` silences it.
- **Skills**: devkit's `plan`, `commit`, `tdd`, `code-review`, `debug`, `refactor`,
  `handoff`, plus the useful parts of [pstack](https://github.com/cursor/plugins/tree/main/pstack)
  via [pstack-claude](https://github.com/michael-denyer/pstack-claude) — `architect`, `how`,
  `why`, `interrogate`, `babysit`, `show-me-your-work`, `unslop` and more. The principles
  live as files under `kick-mode/principles/`, not as skills. Sources and licences:
  [`plugins/kick/NOTICE.md`](plugins/kick/NOTICE.md).
- **Agents** (Claude Code): `kick:worker`, the read-only `kick:reviewer`, and `kick:comment-sicko`.
  Codex has no plugin agents; skills spawn a subagent that reads the agent file first.
- **`interrogate`** is a cross-agent review: an in-process reviewer plus `claude -p` and
  `codex exec`, read-only, judged by the parent. The diff goes to each reviewer's vendor.
- **Models** default to everyday subscription tiers: `opus`/`sonnet` on Claude Code,
  `gpt-6.1-sol`/`gpt-6-luna` on Codex. Heavier models are opt-in through `setup-kick`.
- **Hands-off** work happens only in kick-mode's Autonomous run playbook, which logs every
  decision and stops before anything irreversible.

The `store` plugin (`store@kicklabs`) carries `store-orchestrator` on its own.

**Other agents.** `npx skills add thekicklabs/devkit` installs the same skills for Gemini CLI,
OpenCode and the other agents it supports. Skills only: no agents, hook or rules.

## npx skills, devkit, or the plugin

| | `npx skills` (vercel-labs 1.7) | devkit CLI | `kick` plugin |
| --- | --- | --- | --- |
| Skills | yes, 40+ agents | yes, claude / codex / cursor | yes, Claude Code and Codex |
| Rules, router, stacks | no | yes, through a managed block | no |
| Agents and hooks | no | no | yes |
| Codex global path | `~/.codex/skills` (deprecated) | `~/.agents/skills` | plugin cache |
| Update / uninstall | lockfile + `update` / `remove` | `devkit update` / none | `plugin update` / `uninstall` |
| Machine bootstrap | no | yes | no |
| Needs | Node | uv and a clone | nothing |

The plugin is the only one that ships agents and the routing hook, so it is how skills reach
Claude Code and Codex. devkit keeps what nothing else does: project-aware rules, stacks and
the router, machine bootstrap, and Cursor skills. `npx skills` stays optional, for agents
neither covers.

## Bootstrap a machine

```bash
curl -fsSL https://raw.githubusercontent.com/thekicklabs/devkit/main/install.sh | bash
devkit machine --all          # docker, tailscale, uv, node, gh, claude, codex — skips what's present
devkit install --global --all # skills + rules for every agent under ~
```

`install.sh` clones (or pulls) the repo to `~/.devkit`, links `~/.local/bin/devkit`, and
installs `uv` if missing. The CLI runs from the clone; nothing else is needed on the box.

## Commands

```
devkit list [skills|stacks|rules|machine]
devkit search <words…>                    full-text over every skill, rule and stack file
devkit install                            interactive picker (skills + stacks, then scope, then agents)
devkit install --local [--path DIR] --agent claude,codex,cursor --stack fastapi,react --skill plan
devkit install --global --agent claude,codex --all --yes
devkit install tdd handoff                shortcut: reuses the last scope/agents
devkit update [--no-pull]                 git pull the clone, then re-copy every recorded install
devkit machine [<tool>…|--all]
```

Non-interactive whenever a flag answers the question, `--yes` is passed, or stdin is not a tty.
Selecting a stack pulls in what it `requires` (`fastapi` → `python`, `react` → `typescript`).

## What gets installed where

| Agent | Scope | Skills | Router | Rules |
| --- | --- | --- | --- | --- |
| claude | global | `~/.claude/skills/<name>` → `~/.agents/skills/<name>` | managed block in `~/.claude/CLAUDE.md` | `~/.agents/AGENTS/` |
| claude | local | `.claude/skills/<name>` → `.agents/skills/<name>` | `AGENTS.md` block + `CLAUDE.md` importing it | `AGENTS/` |
| codex | global | `~/.agents/skills/` | managed block in `~/.codex/AGENTS.md` | `~/.agents/AGENTS/` |
| codex | local | `.agents/skills/` | managed block in `AGENTS.md` | `AGENTS/` |
| cursor | global | `~/.agents/skills/` | none — Cursor has no file-based global rules (paste into User Rules) | `~/.agents/AGENTS/` |
| cursor | local | `.agents/skills/` | `.cursor/rules/devkit.mdc` → `AGENTS.md` | `AGENTS/` |

- One copy per scope: skills are **copied** into `.agents/skills/`, which Codex and Cursor
  read directly; Claude does not, so `.claude/skills/<name>` is a relative symlink into it. Rules live
  once under `AGENTS/`; the routers point at them. The repo stays the source of truth —
  `devkit update` pulls and re-copies every install recorded in
  `~/.config/devkit/installs.json`.
- Router files are edited only between `<!-- devkit:start -->` / `<!-- devkit:end -->`.
  Your own content outside the markers is never touched.
- `AGENTS/project.md` is created once per project and never overwritten — that is where
  project-specific facts go.
- `~/.config/devkit/installs.json` records every install and the sha256 of each written
  file; `update` reports which files it changed on disk.

## Layout

```
.claude-plugin/marketplace.json   the kicklabs marketplace for Claude Code
.agents/plugins/marketplace.json  the same marketplace for Codex
plugins/<plugin>/                 a plugin: .claude-plugin/ and .codex-plugin/ manifests, skills/,
                                  and for kick, agents/ and hooks/
plugins/<plugin>/skills/<name>/   agent-agnostic skills (Agent Skills format)
rules/*.md                        generic rules, always installed
stacks/<name>/                    per-stack router + pattern files; frontmatter may declare `requires`
machine/NN-<tool>.sh              idempotent bootstrap steps; `bash script check` decides whether to run
src/devkit/                       the CLI
```

## Adding a skill

`plugins/kick/skills/<name>/SKILL.md` with frontmatter `name` and `description` (the description says
*when* to use it). Add a row to `src/devkit/templates/AGENTS.md.tmpl` if it should be routed,
and to kick-mode's route table if kick-mode should reach it.

Both runtimes cache a plugin by its version, so any change under `plugins/<plugin>/` ships
with a bump of `version` in both of its `plugin.json` files. Try a change without installing
it: `claude --plugin-dir plugins/kick`, and check it with
`claude plugin validate --strict plugins/kick`.

## Adding a stack

`stacks/<name>/AGENTS.md` with frontmatter `name`, `description`, `route` (the "Working on…"
label) and optional `requires: [other]`. Keep the cp-agents shape: `**Read when:**`,
`**Prereq:**`, tables over prose, every rule in exactly one file, links between them.

## Development

```bash
uv run pytest -q && uv run ruff check . && uv run ty check
```
