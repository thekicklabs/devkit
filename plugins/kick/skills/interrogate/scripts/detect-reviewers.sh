#!/bin/sh
# Prints one tab-separated line per reviewer CLI: name, installed|missing, authed|unauthed|unknown, stable|experimental.
set -u

limit() {
  if command -v timeout >/dev/null 2>&1; then
    timeout 20 "$@"
  else
    "$@"
  fi
}

auth() {
  case "$1" in
    claude) limit claude auth status ;;
    codex) limit codex login status ;;
    agent) limit agent status ;;
    opencode) limit opencode auth list ;;
    *) return 2 ;;
  esac
}

for cli in claude codex agent gemini opencode; do
  case "$cli" in
    claude | codex) tier=stable ;;
    *) tier=experimental ;;
  esac
  if ! command -v "$cli" >/dev/null 2>&1; then
    printf '%s\tmissing\tunknown\t%s\n' "$cli" "$tier"
    continue
  fi
  if [ "$cli" = gemini ]; then
    if [ -n "${GEMINI_API_KEY:-}${GOOGLE_API_KEY:-}${GOOGLE_APPLICATION_CREDENTIALS:-}" ]; then
      state=authed
    else
      state=unknown
    fi
  elif auth "$cli" >/dev/null 2>&1; then
    state=authed
  else
    state=unauthed
  fi
  printf '%s\tinstalled\t%s\t%s\n' "$cli" "$state" "$tier"
done
