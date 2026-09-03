#!/usr/bin/env bash
# description: Tailscale via the official install script (prints the 'tailscale up' hint, does not run it)
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v tailscale >/dev/null; }
main() {
  curl -fsSL https://tailscale.com/install.sh | sh
  echo "next: sudo tailscale up"
}
dispatch "$@"
