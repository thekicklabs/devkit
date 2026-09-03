#!/usr/bin/env bash
# description: OpenAI Codex CLI (needs node — run 40-node first)
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v codex >/dev/null; }
main() {
  export PATH="$HOME/.local/share/fnm:$PATH"
  command -v fnm >/dev/null && eval "$(fnm env)"
  npm install -g @openai/codex
}
dispatch "$@"
