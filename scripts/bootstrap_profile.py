#!/usr/bin/env python3
"""Render and install an overlay profile into a concrete HERMES_HOME path."""

from __future__ import annotations

import argparse
import os
import shutil
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
    parser = argparse.ArgumentParser(description="Install a Hermes Telegram overlay profile.")
    parser.add_argument("--profile", default=DEFAULT_PROFILE_NAME, choices=["dev-macos", "prod-devbox"])
    parser.add_argument("--hermes-home", required=True, help="Target HERMES_HOME directory")
    parser.add_argument("--allowed-users", default="", help="Comma-separated Telegram user IDs")
    parser.add_argument("--litellm-base-url", default=DEFAULT_LITELLM_BASE_URL)
    parser.add_argument("--force", action="store_true", help="Overwrite existing config files")
    return parser.parse_args()


def safe_write(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing file without --force: {path}")
    path.write_text(content, encoding="utf-8")


def ensure_plugin_symlink(target_plugins_dir: Path) -> None:
    target_plugins_dir.mkdir(parents=True, exist_ok=True)
    source = REPO_ROOT / "plugins" / "hermes-telegram-overlay"
    target = target_plugins_dir / "hermes-telegram-overlay"
    if target.is_symlink() or target.exists():
        if target.resolve() == source.resolve():
            return
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    os.symlink(source, target, target_is_directory=True)


def main() -> None:
    args = parse_args()
    hermes_home = Path(args.hermes_home).expanduser().resolve()
    hermes_home.mkdir(parents=True, exist_ok=True)

    layout = resolve_workspace_layout(overlay_repo=REPO_ROOT)
    context = ProfileRenderContext(
        profile_name=args.profile,
        hermes_home=hermes_home,
        layout=layout,
        allowed_users=args.allowed_users,
        litellm_base_url=args.litellm_base_url,
    )

    safe_write(hermes_home / "config.yaml", render_profile_config_yaml(context), force=args.force)
    safe_write(hermes_home / ".env.template", build_env_template(context), force=args.force)
    safe_write(hermes_home / "SOUL.md", build_soul_md(), force=args.force)
    context.runtime_dir.mkdir(parents=True, exist_ok=True)
    context.telethon_session_dir.mkdir(parents=True, exist_ok=True)
    (context.runtime_dir / "logs").mkdir(parents=True, exist_ok=True)
    ensure_plugin_symlink(hermes_home / "plugins")

    print(f"Installed overlay profile at {hermes_home}")
    print("Next steps:")
    print(f"1. Copy {hermes_home / '.env.template'} to {hermes_home / '.env'} and fill secrets.")
    print("2. Ensure the overlay virtualenv exists: python3 scripts/bootstrap_env.py")
    print(f"3. Start Hermes with HERMES_HOME={hermes_home} hermes gateway")


if __name__ == "__main__":
    main()

