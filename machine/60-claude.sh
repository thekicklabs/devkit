#!/usr/bin/env bash
# description: Claude Code CLI
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v claude >/dev/null || [ -x "$HOME/.local/bin/claude" ]; }
main() { curl -fsSL https://claude.ai/install.sh | bash; }
dispatch "$@"
