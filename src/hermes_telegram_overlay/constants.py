"""Shared constants for the Hermes Telegram overlay."""

from pathlib import Path

PLUGIN_NAME = "hermes-telegram-overlay"

OPENTWITTER_SERVER_NAME = "opentwitter-mcp"
OPENNEWS_SERVER_NAME = "opennews-mcp"
TG_HISTORY_SERVER_NAME = "tg-history-mcp"

DEFAULT_MODEL = "claude-opus-4-7"
DEFAULT_LITELLM_BASE_URL = "http://127.0.0.1:4000/v1"
DEFAULT_PROFILE_NAME = "dev-macos"
PROD_PROFILE_NAME = "prod-devbox"


def repo_root() -> Path:
    """Return the overlay repository root."""
    return Path(__file__).resolve().parents[2]

