# Sourced by every machine script. Provides: supported, apt_install, run.
set -euo pipefail

supported() {
  [ -r /etc/os-release ] || return 1
  . /etc/os-release
  case "${ID:-}" in debian|ubuntu) return 0 ;; esac
  case "${ID_LIKE:-}" in *debian*) return 0 ;; esac
  return 1
}

require_supported() {
  if ! supported; then
    echo "unsupported distro for $(basename "$0"); skipping" >&2
    exit 0
  fi
}

apt_install() {
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@"
}

# `bash script check` runs check(); anything else runs main().
dispatch() {
  if [ "${1:-}" = "check" ]; then check; else require_supported; main; fi
}
