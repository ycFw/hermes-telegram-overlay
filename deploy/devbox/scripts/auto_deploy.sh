#!/usr/bin/env bash
set -euo pipefail

# File lock to prevent concurrent deploys
LOCKFILE="/tmp/hermes-deploy.lock"
exec 9>"$LOCKFILE"
if ! flock -n 9; then
  echo "[$(date -Iseconds)] Deploy already running, skipping"
  exit 0
fi

cd "$(dirname "$0")/../../.."

LOCAL=$(git rev-parse HEAD)
git fetch --quiet origin main
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
  exit 0
fi

echo "[$(date -Iseconds)] Update detected: $LOCAL -> $REMOTE"

# Run tests on the NEW code before applying it
if git diff --name-only "$LOCAL" "$REMOTE" | grep -q '^pyproject\.toml$'; then
  NEEDS_REINSTALL=1
else
  NEEDS_REINSTALL=0
fi

# Stash any local state, apply new code
git reset --hard origin/main

if [ "$NEEDS_REINSTALL" = "1" ]; then
  .venv/bin/pip install -e . --quiet
fi

if ! .venv/bin/python -m pytest tests -q; then
  echo "[$(date -Iseconds)] Tests failed; rolling back to $LOCAL"
  git reset --hard "$LOCAL"
  if [ "$NEEDS_REINSTALL" = "1" ]; then
    .venv/bin/pip install -e . --quiet
  fi
  exit 1
fi

restart_service() {
  case "$(uname -s)" in
    Linux*)  systemctl --user restart hermes-telegram.service ;;
    Darwin*) launchctl kickstart -k "gui/$(id -u)/com.hermes.telegram" ;;
    *)       echo "Unsupported OS: $(uname -s)"; exit 1 ;;
  esac
}

check_service() {
  case "$(uname -s)" in
    Linux*)  systemctl --user is-active hermes-telegram.service ;;
    Darwin*) launchctl print "gui/$(id -u)/com.hermes.telegram" 2>/dev/null | grep -q "state = running" && echo "active" || echo "inactive" ;;
  esac
}

restart_service
sleep 3
check_service
echo "[$(date -Iseconds)] Deploy succeeded: $REMOTE"
