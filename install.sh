#!/usr/bin/env bash
# curl -fsSL https://raw.githubusercontent.com/<you>/devkit/main/install.sh | bash
set -euo pipefail

DEVKIT_REPO="${DEVKIT_REPO:-https://github.com/thekicklabs/devkit.git}"
DEVKIT_HOME="${DEVKIT_HOME:-$HOME/.devkit}"
BIN_DIR="$HOME/.local/bin"

fetch_tarball() {
  # No git yet: codeload serves a tarball of the branch, one top-level dir inside.
  local tarball="${DEVKIT_REPO%.git}"
  tarball="${tarball/github.com/codeload.github.com}/tar.gz/main"
  mkdir -p "$DEVKIT_HOME"
  curl -fsSL "$tarball" | tar -xz --strip-components=1 -C "$DEVKIT_HOME"
}

if [ -d "$DEVKIT_HOME/.git" ]; then
  git -C "$DEVKIT_HOME" pull --ff-only
elif command -v git >/dev/null 2>&1; then
  git clone --depth 1 "$DEVKIT_REPO" "$DEVKIT_HOME"
else
  fetch_tarball
fi

mkdir -p "$BIN_DIR"
ln -sfn "$DEVKIT_HOME/bin/devkit" "$BIN_DIR/devkit"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Add $BIN_DIR to PATH: export PATH=\"$BIN_DIR:\$PATH\"" ;;
esac

"$BIN_DIR/devkit" --help
