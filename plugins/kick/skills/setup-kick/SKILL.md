---
name: setup-kick
description: Configure kick for this machine — which model fills each role, which agent CLIs interrogate uses as reviewers, the fan-out cap, and whether the SessionStart hook runs. Use for /setup-kick, "configure kick", changing kick's models or reviewers, or turning the hook on or off.
---

# Setup kick

On Codex, read the [platform mapping](../kick-mode/references/codex-tools.md) before following this skill.

Write `${XDG_CONFIG_HOME:-~/.config}/kick/config.md`, the file [models](../kick-mode/references/models.md) defines. Skills `cat` it at run time; nothing else carries the settings.

## 1. Load

`cat` the config if it exists. Its lines are the starting answers; a role it leaves out takes the default from models.md. Keep lines you do not recognize and say so.

## 2. Detect

- **Models.** On Claude Code, the roles take the model names the `Agent` tool accepts (`opus`, `sonnet`, and any other alias the user's plan offers). On Codex, read the `slug` fields in `${CODEX_HOME:-~/.codex}/models_cache.json` to see what this account can run; an older, cheaper tier such as `gpt-5.6-terra` is a fair `fast` choice. Never write a model you have not seen offered or the user has not confirmed.
- **Reviewers.** Run [`../interrogate/scripts/detect-reviewers.sh`](../interrogate/scripts/detect-reviewers.sh). It prints each CLI as installed or missing, its auth state, and whether kick has verified its reviewer command (`stable`) or not (`experimental`).
- **Codex subagents.** On Codex, check `~/.codex/config.toml` for `[features] multi_agent = true`; without it, kick's fan-out steps run one at a time.

## 3. Ask

Ask once, with the current value or default first. Use `AskUserQuestion` on Claude Code and plain text on Codex.

1. **Roles.** Keep the defaults, or name a model for `strong`, `fast`, `panel`, or `reviewer` on either runtime. A heavier model is an opt-in that costs more of the user's plan; say so.
2. **Reviewers.** Which reviewers `interrogate` runs. `self` is the in-process `kick:reviewer` subagent. The default is `self` plus every installed, authed, stable CLI; interrogate skips the CLI of the runtime it is running in. Add an experimental CLI only on request, and say it is unverified.
3. **Fan-out.** The most subagents that run at once. Default `3`.
4. **Session hook.** `on` injects the kick-mode routing mandate at session start; `off` leaves invocation to the user.

## 4. Write

Overwrite the whole file so a rerun converges on the same result. Write every key, one `key: value` per line, in this order:

```
# kick config, written by setup-kick
claude default: inherit
claude strong: opus
claude fast: sonnet
claude panel: opus, sonnet
claude reviewer: opus
codex default: inherit
codex strong: gpt-6.1-sol
codex fast: gpt-6-luna
codex panel: gpt-6.1-sol, gpt-6-luna
codex reviewer: gpt-6.1-sol
reviewers: self, codex, claude
fan-out: 3
session hook: on
```

Read the file back and show it.

## 5. Permissions

`interrogate` runs `review.sh` from the plugin's `skills/interrogate/scripts/`. Offer these, and change nothing the user declines:

- **Claude Code.** Add `Bash(*/interrogate/scripts/review.sh *)` to `permissions.allow` in `~/.claude/settings.json`, keeping the rest of the file, so background reviews run without a prompt.
- **Codex.** A run of `claude -p` needs network and writes to `~/.claude`, so Codex asks for approval each time. Add `prefix_rule(pattern=["<plugin root>/skills/interrogate/scripts/review.sh"], decision="allow")` to `~/.codex/rules/default.rules`, with the absolute plugin root of this install. The root changes when the plugin updates, so rerun this step after an update.

## Reply

The config file as written, the reviewer roster with each CLI's state, the permission changes made or declined, and anything left at its default.
