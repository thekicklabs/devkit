#!/bin/sh
set -eu

here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
skill=$(dirname -- "$here")
config="${XDG_CONFIG_HOME:-$HOME/.config}/kick/config.md"

usage() {
  cat >&2 <<'EOF'
usage: review.sh prepare (--uncommitted | --base <ref> | --pr <number>) < intent.md
       review.sh run <claude|codex|agent|gemini|opencode> <run-dir> [--model M] [--effort E] [--dry-run]
EOF
  exit 2
}

die() {
  echo "review.sh: $*" >&2
  exit 2
}

conf() {
  [ -f "$config" ] || return 0
  sed -n "s/^$1:[[:space:]]*//p" "$config" | tail -n 1 | sed 's/[[:space:]]*$//'
}

# What a read-only reviewer must leave untouched: HEAD, the status, tracked edits, untracked contents.
snapshot() {
  git rev-parse HEAD
  git status --porcelain=v1 --untracked-files=all
  git diff HEAD | cksum
  git ls-files --others --exclude-standard | while IFS= read -r f; do cksum "$f"; done
}

review_sections() {
  awk '/^## /{p = /^## (1\. Read|2\. Look for|3\. Try to disprove|4\. Severity|Constraints)/} p {sub(/^##/, "###"); print}' \
    "$skill/../code-review/SKILL.md"
}

project_rules() {
  for f in AGENTS.md CLAUDE.md AGENTS/*/review.md; do
    [ -f "$f" ] || continue
    printf '\n### %s\n\n' "$f"
    cat "$f"
  done
}

build_prompt() {
  cat "$skill/references/reviewer-prompt.md"
  printf '\n## Intent\n\n'
  cat "$run/intent.md"
  printf '\n## How to review\n\n'
  review_sections
  rules=$(project_rules)
  if [ -n "$rules" ]; then
    printf '\n## Project rules\n%s\n' "$rules"
  fi
  printf '\n## The change\n\nScope: %s. Read the code around it in the repository as you need.\n\n`````diff\n' "$(cat "$run/scope")"
  cat "$run/diff.patch"
  printf '`````\n\n## Output\n\n'
  printf 'Return only a JSON object matching this schema. Severity and confidence use the scales above; category is the dimension, or house_rule; file is relative to the repository root; line is a number or null.\n\n'
  cat "$run/schema.json"
  echo
}

prepare() {
  ref=
  case "${1:-}" in
    --uncommitted) scope=uncommitted ;;
    --base) scope=base ref=${2:?--base needs a ref} ;;
    --pr) scope=pr ref=${2:?--pr needs a number} ;;
    *) usage ;;
  esac
  repo=$(git rev-parse --show-toplevel)
  cd "$repo"
  run="$(git rev-parse --absolute-git-dir)/kick/$(date -u +%Y%m%dT%H%M%SZ)-$$"
  mkdir -p "$run"
  cat >"$run/intent.md"
  if [ ! -s "$run/intent.md" ]; then
    rm -rf "$run"
    die "write the intent paragraph on stdin"
  fi
  case $scope in
    uncommitted)
      {
        git diff HEAD
        git ls-files --others --exclude-standard | while IFS= read -r f; do
          git diff --no-index -- /dev/null "$f" || true
        done
      } >"$run/diff.patch"
      ;;
    base) git diff "$ref...HEAD" >"$run/diff.patch" ;;
    pr) gh pr diff "$ref" >"$run/diff.patch" ;;
  esac
  if [ ! -s "$run/diff.patch" ]; then
    rm -rf "$run"
    die "the $scope diff is empty"
  fi
  printf '%s\n' "$repo" >"$run/repo"
  printf '%s\n' "$scope${ref:+ $ref}" >"$run/scope"
  tr -d '\n' <"$skill/references/findings.schema.json" >"$run/schema.json"
  build_prompt >"$run/prompt.md"
  snapshot >"$run/state"
  echo "$run"
}

run_cli() {
  [ $# -ge 2 ] || usage
  cli=$1 run=$2
  shift 2
  [ -f "$run/prompt.md" ] || die "no prepared run at $run"
  model= effort=high dry=
  while [ $# -gt 0 ]; do
    case $1 in
      --model) model=${2:?--model needs a value} && shift 2 ;;
      --effort) effort=${2:?--effort needs a value} && shift 2 ;;
      --dry-run) dry=1 && shift ;;
      *) usage ;;
    esac
  done
  [ -n "$model" ] || model=$(conf "$cli reviewer")
  repo=$(cat "$run/repo")
  stdin=$run/prompt.md
  case $cli in
    claude)
      set -- claude -p --safe-mode --model "${model:-opus}" --effort "$effort" \
        --tools Read,Grep,Glob --allowedTools Read,Grep,Glob \
        --disallowedTools 'Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch,Read(**/.env),Read(**/.env.*)' \
        --permission-mode dontAsk --strict-mcp-config --no-session-persistence \
        --output-format json --json-schema "$(cat "$run/schema.json")"
      out=$run/claude.json
      ;;
    codex)
      set -- codex exec --sandbox read-only --ephemeral --ignore-user-config -C "$repo" \
        -m "${model:-gpt-6.1-sol}" -c "model_reasoning_effort=$effort" \
        --output-schema "$run/schema.json" -o "$run/codex.json" -
      out=$run/codex.log
      ;;
    agent)
      set -- agent -p --mode ask --trust --output-format json ${model:+--model "$model"} "Follow $run/prompt.md"
      stdin=/dev/null out=$run/agent.json
      ;;
    gemini)
      set -- gemini --approval-mode plan -o json ${model:+-m "$model"} -p "Review per stdin"
      out=$run/gemini.json
      ;;
    opencode)
      set -- opencode run --agent plan --format json ${model:+-m "$model"} "Follow $run/prompt.md"
      stdin=/dev/null out=$run/opencode.json
      ;;
    *) die "unknown reviewer '$cli'" ;;
  esac
  if [ -n "$dry" ]; then
    printf '%s\n' "$@"
    printf '< %s\n> %s\n' "$stdin" "$out"
    return 0
  fi
  limited=
  if command -v timeout >/dev/null 2>&1; then
    set -- timeout -k 10 "${KICK_REVIEW_TIMEOUT:-900}" "$@"
    limited=1
  fi
  cd "$repo"
  export KICK_HOOK=off
  rc=0
  "$@" <"$stdin" >"$out" 2>"$run/$cli.err" || rc=$?
  if ! snapshot | cmp -s - "$run/state"; then
    status=tainted
  elif [ -n "$limited" ] && { [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; }; then
    status=timeout
  elif [ "$rc" -ne 0 ]; then
    status=failed
  else
    status=ok
  fi
  echo "$status" >"$run/$cli.status"
  echo "$cli: $status (exit $rc)"
}

case "${1:-}" in
  prepare) shift && prepare "$@" ;;
  run) shift && run_cli "$@" ;;
  *) usage ;;
esac
