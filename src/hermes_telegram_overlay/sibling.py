"""Resolve the sibling repository layout required by the overlay."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .constants import repo_root


class WorkspaceLayoutError(ValueError):
    """Raised when the overlay sibling repo layout is incomplete."""


@dataclass(frozen=True)
class WorkspaceLayout:
    """Resolved sibling repository paths."""

    overlay_repo: Path
    workspace_root: Path
    hermes_agent_repo: Path
    opentwitter_mcp_repo: Path
    opennews_mcp_repo: Path

    def as_dict(self) -> dict[str, str]:
        """Return the layout as stringified paths."""
        return {
            "overlay_repo": str(self.overlay_repo),
            "workspace_root": str(self.workspace_root),
            "hermes_agent_repo": str(self.hermes_agent_repo),
            "opentwitter_mcp_repo": str(self.opentwitter_mcp_repo),
            "opennews_mcp_repo": str(self.opennews_mcp_repo),
        }


def _resolve_repo_path(
    env: Mapping[str, str],
    env_key: str,
    workspace_root: Path,
    default_name: str,
) -> Path:
    raw = (env.get(env_key) or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return (workspace_root / default_name).resolve()


def resolve_workspace_layout(
    *,
    overlay_repo: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> WorkspaceLayout:
    """Resolve sibling repos for overlay, Hermes, and the two 6551 MCP repos."""
    env = env or {}
    overlay_root = (
        Path((env.get("HERMES_TELEGRAM_OVERLAY_ROOT") or "")).expanduser().resolve()
        if env.get("HERMES_TELEGRAM_OVERLAY_ROOT")
        else (overlay_repo.resolve() if overlay_repo else repo_root().resolve())
    )
    workspace_root = overlay_root.parent

    layout = WorkspaceLayout(
        overlay_repo=overlay_root,
        workspace_root=workspace_root,
        hermes_agent_repo=_resolve_repo_path(env, "HERMES_AGENT_REPO", workspace_root, "hermes-agent"),
        opentwitter_mcp_repo=_resolve_repo_path(env, "OPENTWITTER_MCP_REPO", workspace_root, "opentwitter-mcp"),
        opennews_mcp_repo=_resolve_repo_path(env, "OPENNEWS_MCP_REPO", workspace_root, "opennews-mcp"),
    )

    missing = [
        ("hermes-agent", layout.hermes_agent_repo),
        ("opentwitter-mcp", layout.opentwitter_mcp_repo),
        ("opennews-mcp", layout.opennews_mcp_repo),
    ]
    missing = [(name, path) for name, path in missing if not path.exists()]
    if missing:
        lines = [
            "Overlay sibling repo layout is incomplete.",
            f"Expected sibling repos under: {layout.workspace_root}",
            f"- hermes-telegram-overlay: {layout.overlay_repo}",
        ]
        lines.extend(f"- {name}: {path}" for name, path in missing)
        lines.append("You can override paths with HERMES_AGENT_REPO / OPENTWITTER_MCP_REPO / OPENNEWS_MCP_REPO.")
        raise WorkspaceLayoutError("\n".join(lines))

    return layout

