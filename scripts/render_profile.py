#!/usr/bin/env python3
"""Render a profile bundle without modifying the user's Hermes installation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hermes_telegram_overlay.constants import DEFAULT_LITELLM_BASE_URL, DEFAULT_PROFILE_NAME
from hermes_telegram_overlay.profiles import (
    ProfileRenderContext,
    build_env_template,
    build_soul_md,
    render_profile_config_yaml,
)
from hermes_telegram_overlay.sibling import resolve_workspace_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a Hermes Telegram overlay profile bundle.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE_NAME, choices=["dev-macos", "prod-devbox"])
    parser.add_argument("--output-dir", required=True, help="Directory to receive config.yaml, .env.template, and SOUL.md")
    parser.add_argument("--allowed-users", default="", help="Comma-separated Telegram user IDs")
    parser.add_argument("--litellm-base-url", default=DEFAULT_LITELLM_BASE_URL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    layout = resolve_workspace_layout(overlay_repo=REPO_ROOT)
    context = ProfileRenderContext(
        profile_name=args.profile,
        hermes_home=output_dir,
        layout=layout,
        allowed_users=args.allowed_users,
        litellm_base_url=args.litellm_base_url,
    )

    (output_dir / "config.yaml").write_text(render_profile_config_yaml(context), encoding="utf-8")
    (output_dir / ".env.template").write_text(build_env_template(context), encoding="utf-8")
    (output_dir / "SOUL.md").write_text(build_soul_md(), encoding="utf-8")

    print(f"Rendered profile bundle to {output_dir}")


if __name__ == "__main__":
    main()

