#!/usr/bin/env bash
# description: Node LTS via fnm
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { [ -x "$HOME/.local/share/fnm/fnm" ] || command -v fnm >/dev/null; }
main() {
  curl -fsSL https://fnm.vercel.app/install | bash -s -- --skip-shell
  export PATH="$HOME/.local/share/fnm:$PATH"
  eval "$(fnm env)"
  fnm install --lts
  fnm default lts-latest
  echo "add to your shell rc:  eval \"\$(fnm env --use-on-cd)\""
}
dispatch "$@"
