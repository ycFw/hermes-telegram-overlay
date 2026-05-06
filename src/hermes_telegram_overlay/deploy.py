"""Render Dev Box deployment templates for the overlay."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

UNRESOLVED_PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")


class DeployTemplateError(ValueError):
    """Raised when a deployment template cannot be rendered cleanly."""


@dataclass(frozen=True)
class DevboxDeployContext:
    """Concrete values used to render Dev Box deployment assets."""

    overlay_repo: str
    hermes_home: str
    heartbeat_path: str = r"$env:LOCALAPPDATA\HermesTelegram\heartbeat.json"
    wsl_distro: str = "Ubuntu"
    service_name: str = "hermes-telegram.service"
    boot_task_name: str = "HermesTelegramBoot"

    def replacements(self) -> dict[str, str]:
        return {
            "__OVERLAY_REPO__": self.overlay_repo,
            "__HERMES_HOME__": self.hermes_home,
            "__HEARTBEAT_PATH__": self.heartbeat_path,
            "__WSL_DISTRO__": self.wsl_distro,
            "__SERVICE_NAME__": self.service_name,
            "__BOOT_TASK_NAME__": self.boot_task_name,
        }


DEPLOY_TEMPLATES: dict[Path, Path] = {
    Path("deploy/devbox/systemd/hermes-telegram.service"): Path("systemd/hermes-telegram.service"),
    Path("deploy/devbox/systemd/hermes-telegram-deploy.service"): Path("systemd/hermes-telegram-deploy.service"),
    Path("deploy/devbox/systemd/hermes-telegram-deploy.timer"): Path("systemd/hermes-telegram-deploy.timer"),
    Path("deploy/devbox/windows/Watch-HermesTelegram.ps1"): Path("windows/Watch-HermesTelegram.ps1"),
    Path("deploy/devbox/windows/Get-HermesTelegramStatus.ps1"): Path("windows/Get-HermesTelegramStatus.ps1"),
}


def render_deploy_template(template_text: str, context: DevboxDeployContext) -> str:
    """Replace all supported placeholders inside a deployment template."""
    rendered = template_text
    for placeholder, value in context.replacements().items():
        rendered = rendered.replace(placeholder, value)

    unresolved = sorted(set(UNRESOLVED_PLACEHOLDER_RE.findall(rendered)))
    if unresolved:
        raise DeployTemplateError(f"Unresolved deployment placeholders: {', '.join(unresolved)}")
    return rendered


def render_devbox_bundle(
    *,
    repo_root: Path,
    output_dir: Path,
    context: DevboxDeployContext,
) -> dict[str, str]:
    """Render all deployment templates into a concrete output directory."""
    written: dict[str, str] = {}
    for source_relative, target_relative in DEPLOY_TEMPLATES.items():
        source_path = repo_root / source_relative
        target_path = output_dir / target_relative
        target_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = render_deploy_template(source_path.read_text(encoding="utf-8"), context)
        target_path.write_text(rendered, encoding="utf-8")
        written[str(target_relative)] = str(target_path)
    return written
