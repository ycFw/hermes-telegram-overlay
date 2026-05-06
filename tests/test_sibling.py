from pathlib import Path

from hermes_telegram_overlay.sibling import WorkspaceLayoutError, resolve_workspace_layout


def test_resolve_workspace_layout_with_siblings(tmp_path):
    overlay = tmp_path / "hermes-telegram-overlay"
    overlay.mkdir()
    (tmp_path / "hermes-agent").mkdir()
    (tmp_path / "opentwitter-mcp").mkdir()
    (tmp_path / "opennews-mcp").mkdir()

    layout = resolve_workspace_layout(overlay_repo=overlay)

    assert layout.overlay_repo == overlay.resolve()
    assert layout.hermes_agent_repo == (tmp_path / "hermes-agent").resolve()


def test_resolve_workspace_layout_reports_missing_repos(tmp_path):
    overlay = tmp_path / "hermes-telegram-overlay"
    overlay.mkdir()

    try:
        resolve_workspace_layout(overlay_repo=overlay)
    except WorkspaceLayoutError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected WorkspaceLayoutError")

    assert "Overlay sibling repo layout is incomplete." in message
    assert "hermes-agent" in message
    assert "opentwitter-mcp" in message
    assert "opennews-mcp" in message

