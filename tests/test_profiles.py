from pathlib import Path

from hermes_telegram_overlay.constants import DEFAULT_MODEL
from hermes_telegram_overlay.profiles import ProfileRenderContext, build_profile_config
from hermes_telegram_overlay.sibling import WorkspaceLayout


def make_layout(tmp_path: Path) -> WorkspaceLayout:
    return WorkspaceLayout(
        overlay_repo=tmp_path / "hermes-telegram-overlay",
        workspace_root=tmp_path,
        hermes_agent_repo=tmp_path / "hermes-agent",
        opentwitter_mcp_repo=tmp_path / "opentwitter-mcp",
        opennews_mcp_repo=tmp_path / "opennews-mcp",
    )


def test_build_profile_config_contains_fixed_model_and_toolsets(tmp_path):
    layout = make_layout(tmp_path)
    context = ProfileRenderContext(
        profile_name="dev-macos",
        hermes_home=tmp_path / ".hermes" / "profiles" / "dev",
        layout=layout,
        allowed_users="123,456",
    )

    config = build_profile_config(context)

    assert config["model"]["default"] == DEFAULT_MODEL
    assert config["model"]["provider"] == "custom"
    assert config["model"]["api_mode"] == "chat_completions"
    assert config["plugins"]["enabled"] == ["hermes-telegram-overlay"]
    assert config["platform_toolsets"]["telegram"] == [
        "memory",
        "skills",
        "web",
        "mcp-opentwitter-mcp",
        "mcp-opennews-mcp",
        "mcp-tg-history-mcp",
    ]
    assert config["unauthorized_dm_behavior"] == "ignore"
    assert "tg-history-mcp" in config["mcp_servers"]

