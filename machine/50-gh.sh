#!/usr/bin/env bash
# description: GitHub CLI from the official apt repo
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v gh >/dev/null; }
main() {
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null
  sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  apt_install gh
  echo "next: gh auth login"
}
dispatch "$@"
