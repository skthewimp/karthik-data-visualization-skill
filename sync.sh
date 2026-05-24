#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$repo_dir"

pull=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-pull)
      pull=0
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./sync.sh [--no-pull]

Pull latest changes, build Codex and Claude copies, and install the public
karthik-data-visualization skill to ~/.codex/skills and ~/.claude/skills.
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

python3 sync-skills.py
