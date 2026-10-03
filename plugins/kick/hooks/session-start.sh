#!/bin/sh
set -eu

case "${1:-}" in
  claude) skill='the `kick:kick-mode` skill' ;;
  codex) skill='the `$kick:kick-mode` skill' ;;
  *)
    echo "session-start.sh: unknown runtime '${1:-}' (expected claude or codex)" >&2
    exit 2
    ;;
esac

# Codex also reads hooks/hooks.json and, unlike Claude Code, exports PLUGIN_ROOT;
# leave Codex to codex-hooks.json so the mandate is injected once.
if [ "$1" = claude ] && [ -n "${PLUGIN_ROOT:-}" ]; then
  exit 0
fi

if [ "${KICK_HOOK:-on}" = off ]; then
  exit 0
fi

config="${XDG_CONFIG_HOME:-$HOME/.config}/kick/config.md"
if grep -qsE '^session hook:[[:space:]]*off[[:space:]]*$' "$config"; then
  exit 0
fi

sed -e "s|{{SKILL}}|$skill|" -e "s|{{CONFIG}}|$config|" "$(dirname "$0")/session-start-context.md"
