from pathlib import Path

from hermes_telegram_overlay.deploy import DevboxDeployContext, render_deploy_template, render_devbox_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_render_deploy_template_replaces_all_placeholders():
    context = DevboxDeployContext(
        overlay_repo="/home/dev/hermes-telegram-overlay",
        hermes_home="/home/dev/.hermes/profiles/hermes-telegram-prod",
        heartbeat_path=r"$env:LOCALAPPDATA\HermesTelegram\heartbeat.json",
        wsl_distro="Ubuntu-24.04",
        service_name="hermes-telegram.service",
        boot_task_name="HermesTelegramBoot",
    )

    rendered = render_deploy_template(
        "repo=__OVERLAY_REPO__ home=__HERMES_HOME__ distro=__WSL_DISTRO__ heartbeat=__HEARTBEAT_PATH__",
        context,
    )

    assert "__OVERLAY_REPO__" not in rendered
    assert "__HERMES_HOME__" not in rendered
    assert "Ubuntu-24.04" in rendered
    assert r"$env:LOCALAPPDATA\HermesTelegram\heartbeat.json" in rendered


def test_render_devbox_bundle_writes_expected_files(tmp_path: Path):
    context = DevboxDeployContext(
        overlay_repo="/home/dev/hermes-telegram-overlay",
        hermes_home="/home/dev/.hermes/profiles/hermes-telegram-prod",
    )

    written = render_devbox_bundle(
        repo_root=REPO_ROOT,
        output_dir=tmp_path,
        context=context,
    )

    assert set(written) == {
        "systemd/hermes-telegram.service",
        "systemd/hermes-telegram-deploy.service",
        "systemd/hermes-telegram-deploy.timer",
        "windows/Watch-HermesTelegram.ps1",
        "windows/Get-HermesTelegramStatus.ps1",
    }
    service_text = (tmp_path / "systemd" / "hermes-telegram.service").read_text(encoding="utf-8")
    watch_text = (tmp_path / "windows" / "Watch-HermesTelegram.ps1").read_text(encoding="utf-8")
    deploy_service_text = (tmp_path / "systemd" / "hermes-telegram-deploy.service").read_text(encoding="utf-8")
    timer_text = (tmp_path / "systemd" / "hermes-telegram-deploy.timer").read_text(encoding="utf-8")
    assert "/home/dev/hermes-telegram-overlay" in service_text
    assert "/home/dev/.hermes/profiles/hermes-telegram-prod" in service_text
    assert "__HEARTBEAT_PATH__" not in watch_text
    assert "/home/dev/hermes-telegram-overlay/deploy/devbox/scripts/auto_deploy.sh" in deploy_service_text
    assert "deploy.log" in deploy_service_text
    assert "OnUnitActiveSec=60s" in timer_text


def test_auto_deploy_script_is_executable_and_well_formed():
    script_path = REPO_ROOT / "deploy" / "devbox" / "scripts" / "auto_deploy.sh"
    assert script_path.exists()
    text = script_path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in text
    assert "git fetch --quiet origin main" in text
    assert "git reset --hard origin/main" in text
    assert "pytest tests -q" in text
    assert "systemctl --user restart hermes-telegram.service" in text
