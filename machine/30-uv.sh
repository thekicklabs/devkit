#!/usr/bin/env bash
# description: uv (Python package manager) into ~/.local/bin
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v uv >/dev/null || [ -x "$HOME/.local/bin/uv" ]; }
main() { curl -LsSf https://astral.sh/uv/install.sh | sh; }
dispatch "$@"
