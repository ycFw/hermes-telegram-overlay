#!/usr/bin/env python3
"""Render Dev Box deployment templates with concrete runtime paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hermes_telegram_overlay.deploy import DevboxDeployContext, render_devbox_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Dev Box deployment templates for Hermes Telegram overlay.")
    parser.add_argument(
        "--overlay-repo",
        default=str(REPO_ROOT),
        help="Runtime overlay repository path on the target machine, typically a WSL path.",
    )
    parser.add_argument(
        "--hermes-home",
        required=True,
        help="Runtime HERMES_HOME path on the target machine, typically a WSL path.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory to receive rendered systemd/PowerShell assets")
    parser.add_argument(
        "--heartbeat-path",
        default=r"$env:LOCALAPPDATA\HermesTelegram\heartbeat.json",
        help="Windows path used by the watchdog/status scripts to persist heartbeat state.",
    )
    parser.add_argument("--wsl-distro", default="Ubuntu")
    parser.add_argument("--service-name", default="hermes-telegram.service")
    parser.add_argument("--boot-task-name", default="HermesTelegramBoot")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    context = DevboxDeployContext(
        overlay_repo=args.overlay_repo,
        hermes_home=args.hermes_home,
        heartbeat_path=args.heartbeat_path,
        wsl_distro=args.wsl_distro,
        service_name=args.service_name,
        boot_task_name=args.boot_task_name,
    )
    written = render_devbox_bundle(repo_root=REPO_ROOT, output_dir=output_dir, context=context)
    print(json.dumps({"output_dir": str(output_dir), "files": written}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
