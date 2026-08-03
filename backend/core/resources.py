"""Locate application resources in source and PyInstaller builds."""

import os
import sys
from pathlib import Path


def application_root() -> Path:
    """Return the source root or PyInstaller's immutable bundle directory."""

    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    return application_root().joinpath(*parts)


def configured_tool(environment_name: str, executable_name: str) -> str:
    """Prefer an explicit override, then the bundled executable, then PATH."""

    configured = os.getenv(environment_name, "").strip()
    if configured:
        return str(Path(configured).expanduser())
    suffix = ".exe" if os.name == "nt" else ""
    bundled = resource_path("tools", f"{executable_name}{suffix}")
    return str(bundled) if bundled.is_file() else executable_name
