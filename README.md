# devkit

One repo that sets up a machine and every coding agent on it the same way: shared skills,
one set of working rules, per-stack conventions — copied into the right place for Claude
Code, Codex and Cursor — plus the bootstrap scripts for a fresh Debian/Ubuntu VM.

## Bootstrap a machine

```bash
curl -fsSL https://raw.githubusercontent.com/thekicklabs/devkit/main/install.sh | bash
devkit machine --all          # docker, tailscale, uv, node, gh, claude, codex — skips what's present
devkit install --global --all # skills + rules for claude and codex under ~
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
devkit machine [<tool>…|--all]
```

Non-interactive whenever a flag answers the question, `--yes` is passed, or stdin is not a tty.
Selecting a stack pulls in what it `requires` (`fastapi` → `python`, `react` → `typescript`).

## What gets installed where

| Agent | Scope | Skills | Router | Rules |
| --- | --- | --- | --- | --- |
| claude | global | `~/.claude/skills/` | managed block in `~/.claude/CLAUDE.md` | `~/.agents/AGENTS/` |
| claude | local | `.claude/skills/` | `AGENTS.md` block + `CLAUDE.md` importing it | `AGENTS/` |
| codex | global | `~/.agents/skills/` | managed block in `~/.codex/AGENTS.md` | `~/.agents/AGENTS/` |
| codex | local | `.agents/skills/` | managed block in `AGENTS.md` | `AGENTS/` |
| cursor | local | `.cursor/skills/` | `.cursor/rules/devkit.mdc` → `AGENTS.md` | `AGENTS/` |

- Everything is **copied**; the repo stays the source of truth. Re-run `install` to refresh.
- Router files are edited only between `<!-- devkit:start -->` / `<!-- devkit:end -->`.
  Your own content outside the markers is never touched.
- `AGENTS/project.md` is created once per project and never overwritten — that is where
  project-specific facts go.
- `~/.config/devkit/installs.json` records every written path and its sha256.

## Layout

```
skills/<name>/SKILL.md      agent-agnostic skills (Agent Skills format)
rules/*.md                  generic rules, always installed
stacks/<name>/              per-stack router + pattern files; frontmatter may declare `requires`
machine/NN-<tool>.sh        idempotent bootstrap steps; `bash script check` decides whether to run
src/devkit/                 the CLI
```

## Adding a skill

`skills/<name>/SKILL.md` with frontmatter `name` and `description` (the description says
*when* to use it). Add a row to `src/devkit/templates/AGENTS.md.tmpl` if it should be routed.

## Adding a stack

`stacks/<name>/AGENTS.md` with frontmatter `name`, `description`, `route` (the "Working on…"
label) and optional `requires: [other]`. Keep the cp-agents shape: `**Read when:**`,
`**Prereq:**`, tables over prose, every rule in exactly one file, links between them.

## Development

```bash
uv run pytest -q && uv run ruff check . && uv run ty check
```
