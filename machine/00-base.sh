#!/usr/bin/env bash
# description: git, curl, build-essential, unzip, ca-certificates
. "$(dirname "$(readlink -f "$0")")/_lib.sh"

check() { command -v git >/dev/null && command -v curl >/dev/null && command -v gcc >/dev/null && command -v unzip >/dev/null; }
main() { apt_install git curl build-essential unzip ca-certificates gnupg; }
dispatch "$@"
