#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../../.."

LOCAL=$(git rev-parse HEAD)
git fetch --quiet origin main
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  exit 0
fi

echo "[$(date -Iseconds)] Update detected: $LOCAL -> $REMOTE"

if git diff --name-only "$LOCAL" "$REMOTE" | grep -q '^pyproject\.toml$'; then
  NEEDS_REINSTALL=1
else
  NEEDS_REINSTALL=0
fi

git reset --hard origin/main

if [ "$NEEDS_REINSTALL" = "1" ]; then
  .venv/bin/pip install -e . --quiet
fi

if ! .venv/bin/python -m pytest tests -q; then
  echo "[$(date -Iseconds)] Tests failed; aborting deploy. Old service still running."
  exit 1
fi

systemctl --user restart hermes-telegram.service
sleep 3
systemctl --user is-active hermes-telegram.service
echo "[$(date -Iseconds)] Deploy succeeded: $REMOTE"
