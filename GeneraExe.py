"""Rigenera la distribuzione portabile di Audio Track Studio."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def find_powershell() -> str | None:
    """Restituisce PowerShell 7, oppure Windows PowerShell se disponibile."""
    return shutil.which("pwsh") or shutil.which("powershell")


def main() -> int:
    project_root = Path(__file__).resolve().parent
    build_script = project_root / "scripts" / "build_release.ps1"

    if not build_script.is_file():
        print(f"ERRORE: script di build non trovato: {build_script}", file=sys.stderr)
        return 1

    powershell = find_powershell()
    if powershell is None:
        print(
            "ERRORE: PowerShell non e' disponibile nel PATH di sistema.",
            file=sys.stderr,
        )
        return 1

    command = [
        powershell,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(build_script),
    ]

    print("Rigenerazione di Audio Track Studio in corso...")
    print(f"Script: {build_script}")

    try:
        result = subprocess.run(command, cwd=project_root, check=False)
    except OSError as exc:
        print(f"ERRORE: impossibile avviare PowerShell: {exc}", file=sys.stderr)
        return 1

    if result.returncode != 0:
        print(
            f"\nBuild non riuscita (codice {result.returncode}).",
            file=sys.stderr,
        )
        return result.returncode

    print("\nBuild completata correttamente.")
    print(
        "Versione portabile: "
        "dist\\Audio Track Studio\\Audio Track Studio.exe"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
