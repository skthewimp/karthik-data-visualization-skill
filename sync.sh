#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

pull=1
sync_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-pull)
      pull=0
      shift
      ;;
    --validate-only|--surface)
      sync_args+=("$1")
      if [[ "$1" == "--surface" ]]; then
        if [[ $# -lt 2 ]]; then
          echo "--surface requires all, codex, or claude" >&2
          exit 2
        fi
        sync_args+=("$2")
        shift
      fi
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./sync.sh [--no-pull] [--validate-only] [--surface all|codex|claude]

Pull latest changes and install the public data visualization skills to
~/.codex/skills and ~/.claude/skills.
EOF
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "$pull" -eq 1 ]]; then
  git pull --ff-only
fi

if [[ "${#sync_args[@]}" -gt 0 ]]; then
  python3 sync-skills.py "${sync_args[@]}"
else
  python3 sync-skills.py
fi
