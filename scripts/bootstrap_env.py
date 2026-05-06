#!/usr/bin/env python3
"""Create the overlay virtualenv and install local editable packages."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hermes_telegram_overlay.sibling import resolve_workspace_layout

MIN_PYTHON = (3, 10)
PYTHON_CANDIDATES = ("python3.13", "python3.12", "python3.11", "python3.10", "python3")
PIP_BOOTSTRAP_PACKAGES = ("pip>=23.3", "setuptools>=68", "wheel>=0.43")


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def capture(cmd: list[str]) -> str:
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the overlay virtualenv and install dependencies.")
    parser.add_argument(
        "--python",
        default="",
        help="Python executable to use for the virtualenv. Defaults to auto-discovery of Python >= 3.10.",
    )
    return parser.parse_args()


def _resolve_python_candidate(candidate: str) -> str | None:
    if not candidate:
        return None

    raw_path = Path(candidate).expanduser()
    if raw_path.exists():
        return str(raw_path.resolve())

    discovered = shutil.which(candidate)
    return discovered


def _read_python_version(python_bin: str) -> tuple[int, int]:
    raw = capture(
        [
            python_bin,
            "-c",
            "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')",
        ]
    )
    major_text, minor_text = raw.split(".", 1)
    return int(major_text), int(minor_text)


def _version_text(version: tuple[int, int]) -> str:
    return f"{version[0]}.{version[1]}"


def find_python_executable(explicit: str = "") -> str:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)

    env_python = (os.getenv("HERMES_OVERLAY_PYTHON") or "").strip()
    if env_python:
        candidates.append(env_python)

    candidates.extend(PYTHON_CANDIDATES)

    seen: set[str] = set()
    incompatible: list[str] = []

    for candidate in candidates:
        resolved = _resolve_python_candidate(candidate)
        if not resolved or resolved in seen:
            continue
        seen.add(resolved)

        try:
            version = _read_python_version(resolved)
        except Exception:
            continue

        if version >= MIN_PYTHON:
            return resolved
        incompatible.append(f"{resolved} (found {_version_text(version)})")

    details = "\n".join(f"- {item}" for item in incompatible) if incompatible else "- no usable python executable found"
    raise SystemExit(
        "No Python >= 3.10 interpreter is available for the overlay environment.\n"
        "Install python3.10+ or pass --python /path/to/python.\n"
        f"Checked:\n{details}"
    )


def ensure_venv(venv_dir: Path, python_bin: str) -> Path:
    venv_python = venv_dir / "bin" / "python"
    recreate = not venv_python.exists()

    if not recreate:
        try:
            recreate = _read_python_version(str(venv_python)) != _read_python_version(python_bin)
        except Exception:
            recreate = True

    cmd = [python_bin, "-m", "venv"]
    if recreate and venv_dir.exists():
        cmd.append("--clear")
    cmd.append(str(venv_dir))
    if recreate or not venv_dir.exists():
        run(cmd)

    return venv_python


def pip_install(python_bin: Path, *args: str) -> None:
    cache_dir = REPO_ROOT / ".cache" / "pip"
    cache_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PIP_CACHE_DIR"] = str(cache_dir)
    run([str(python_bin), "-m", "pip", *args], env=env)


def ensure_build_tooling(python_bin: Path) -> None:
    try:
        pip_install(python_bin, "install", "--upgrade", *PIP_BOOTSTRAP_PACKAGES)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Failed to bootstrap pip/setuptools/wheel for the overlay virtualenv. "
            "Check network access and rerun."
        ) from exc


def main() -> None:
    args = parse_args()
    layout = resolve_workspace_layout(overlay_repo=REPO_ROOT)
    venv_dir = REPO_ROOT / ".venv"
    source_python = find_python_executable(args.python)
    python_bin = ensure_venv(venv_dir, source_python)
    ensure_build_tooling(python_bin)

    packages = [
        f"{REPO_ROOT}[dev]",
        str(layout.opentwitter_mcp_repo),
        str(layout.opennews_mcp_repo),
    ]
    for package in packages:
        pip_install(python_bin, "install", "-e", package)

    print("Overlay environment is ready.")
    print(f"Source Python: {source_python}")
    print(f"Python: {python_bin}")


if __name__ == "__main__":
    main()
