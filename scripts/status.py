#!/usr/bin/env python3
"""Show visible profile/runtime status for the overlay."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hermes_telegram_overlay.sibling import resolve_workspace_layout


def tail_lines(path: Path, line_count: int = 20) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()[-line_count:]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show Hermes Telegram overlay status.")
    parser.add_argument("--hermes-home", required=True, help="Profile HERMES_HOME directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    hermes_home = Path(args.hermes_home).expanduser().resolve()
    runtime_dir = hermes_home / "runtime"
    heartbeat_path = runtime_dir / "heartbeat.json"
    gateway_log = runtime_dir / "logs" / "gateway.log"
    err_log = runtime_dir / "logs" / "gateway.err.log"
    layout = resolve_workspace_layout(overlay_repo=REPO_ROOT)

    heartbeat = {}
    if heartbeat_path.exists():
        try:
            heartbeat = json.loads(heartbeat_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            heartbeat = {"error": f"heartbeat file is not valid JSON: {heartbeat_path}"}

    report = {
        "overlay_repo": str(REPO_ROOT),
        "workspace_layout": layout.as_dict(),
        "hermes_home": str(hermes_home),
        "config_exists": (hermes_home / "config.yaml").exists(),
        "env_exists": (hermes_home / ".env").exists(),
        "plugin_link_exists": (hermes_home / "plugins" / "hermes-telegram-overlay").exists(),
        "overlay_venv_exists": (REPO_ROOT / ".venv" / "bin" / "python").exists(),
        "telethon_session_dir_exists": (runtime_dir / "telethon").exists(),
        "heartbeat": heartbeat,
        "recent_gateway_log": tail_lines(gateway_log),
        "recent_gateway_err_log": tail_lines(err_log),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

