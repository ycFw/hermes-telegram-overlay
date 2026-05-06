"""Profile rendering helpers for dev-macos and prod-devbox."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent

from .constants import (
    DEFAULT_LITELLM_BASE_URL,
    DEFAULT_PROFILE_NAME,
    OPENNEWS_SERVER_NAME,
    OPENTWITTER_SERVER_NAME,
    PLUGIN_NAME,
    PROD_PROFILE_NAME,
    TG_HISTORY_SERVER_NAME,
)
from .model_config import build_model_config
from .sibling import WorkspaceLayout


def _mcp_toolset_name(server_name: str) -> str:
    return f"mcp-{server_name}"


@dataclass(frozen=True)
class ProfileRenderContext:
    """Concrete rendering inputs for a Hermes profile."""

    profile_name: str
    hermes_home: Path
    layout: WorkspaceLayout
    allowed_users: str = ""
    litellm_base_url: str = DEFAULT_LITELLM_BASE_URL
    runtime_dir_name: str = "runtime"

    @property
    def runtime_dir(self) -> Path:
        return self.hermes_home / self.runtime_dir_name

    @property
    def telethon_session_dir(self) -> Path:
        return self.runtime_dir / "telethon"


def build_soul_md() -> str:
    """Return the fixed overlay SOUL.md content."""
    return dedent(
        """\
        你是一个中文优先的 Telegram 助手。

        回答要求：
        - 默认使用中文。
        - 结论先行，废话最少。
        - 育儿、健康、安全相关问题必须保守，不给高风险建议。
        - 不编造外部事实；不确定时明确说不确定。
        - 当用户询问 X、新闻、Telegram 频道内容时，优先使用已接入的工具。

        场景偏好：
        - 育儿与家庭日常
        - 工作与效率
        - 一般知识问答
        """
    )


def build_env_template(context: ProfileRenderContext) -> str:
    """Render a profile-scoped `.env` template."""
    bot_hint = "staging bot token" if context.profile_name == DEFAULT_PROFILE_NAME else "production bot token"
    return dedent(
        f"""\
        # Fill this file before starting the gateway.
        # For {context.profile_name}, use the {bot_hint}.

        TELEGRAM_BOT_TOKEN=
        TELEGRAM_ALLOWED_USERS={context.allowed_users}

        # LiteLLM custom OpenAI-compatible endpoint auth
        OPENAI_API_KEY=

        # Telethon user session for tg-history-mcp
        TG_HISTORY_API_ID=
        TG_HISTORY_API_HASH=
        TG_HISTORY_SESSION_DIR={context.telethon_session_dir}
        TG_HISTORY_SESSION_NAME={context.profile_name}
        """
    )


def _mcp_server(command_python: str, repo_src: Path, module_name: str) -> dict:
    return {
        "command": command_python,
        "args": ["-m", module_name],
        "env": {"PYTHONPATH": str(repo_src)},
        "enabled": True,
        "timeout": 180,
        "connect_timeout": 30,
        "tools": {"resources": False, "prompts": False},
    }


def build_profile_config(context: ProfileRenderContext) -> dict:
    """Build the rendered config object for a Hermes profile."""
    overlay_python = str(context.layout.overlay_repo / ".venv" / "bin" / "python")
    if context.profile_name == PROD_PROFILE_NAME:
        terminal_cwd = str(context.layout.overlay_repo)
    else:
        terminal_cwd = str(context.layout.overlay_repo)

    config: dict = {}
    config.update(build_model_config(context.litellm_base_url))
    config.update(
        {
            "agent": {"reasoning_effort": "high"},
            "terminal": {"backend": "local", "cwd": terminal_cwd, "timeout": 180},
            "memory": {"memory_enabled": True, "user_profile_enabled": True},
            "plugins": {"enabled": [PLUGIN_NAME]},
            "platform_toolsets": {
                "telegram": [
                    "hermes-telegram",
                    _mcp_toolset_name(OPENTWITTER_SERVER_NAME),
                    _mcp_toolset_name(OPENNEWS_SERVER_NAME),
                    _mcp_toolset_name(TG_HISTORY_SERVER_NAME),
                ]
            },
            "unauthorized_dm_behavior": "ignore",
            "streaming": {"enabled": True, "transport": "edit"},
            "telegram": {
                "require_mention": True,
                "reactions": True,
                "mention_patterns": [],
                "ignored_threads": [],
                "free_response_chats": [],
            },
            "platforms": {
                "telegram": {
                    "extra": {
                        "unauthorized_dm_behavior": "ignore",
                    }
                }
            },
            "mcp_servers": {
                OPENTWITTER_SERVER_NAME: _mcp_server(
                    overlay_python,
                    context.layout.opentwitter_mcp_repo / "src",
                    "opentwitter_mcp",
                ),
                OPENNEWS_SERVER_NAME: _mcp_server(
                    overlay_python,
                    context.layout.opennews_mcp_repo / "src",
                    "opennews_mcp",
                ),
                TG_HISTORY_SERVER_NAME: _mcp_server(
                    overlay_python,
                    context.layout.overlay_repo / "src",
                    "hermes_telegram_overlay.mcp_server",
                ),
            },
        }
    )
    return config


def render_profile_config_yaml(context: ProfileRenderContext) -> str:
    """Render profile config.yaml text."""
    import yaml

    return yaml.safe_dump(build_profile_config(context), sort_keys=False, allow_unicode=True)

