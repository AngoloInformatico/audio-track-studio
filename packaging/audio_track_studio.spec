# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(SPEC).resolve().parent.parent
frontend = root / "frontend" / "dist"
icon = root / "Icon" / "icon.ico"

if not (frontend / "index.html").is_file():
    raise SystemExit("Frontend non compilato: esegui npm run build.")
if not icon.is_file():
    raise SystemExit("Icon/icon.ico non trovato.")


def works_after_copy(source):
    """Reject package-manager shims that break once moved into the release."""

    try:
        with tempfile.TemporaryDirectory(prefix="ats-tool-check-") as temporary:
            copied = Path(temporary) / source.name
            shutil.copy2(source, copied)
            result = subprocess.run(
                [str(copied), "-version"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def path_candidates(executable_name):
    names = [executable_name]
    if os.name == "nt" and not executable_name.lower().endswith(".exe"):
        names.insert(0, f"{executable_name}.exe")
    seen = set()
    for raw_directory in os.environ.get("PATH", "").split(os.pathsep):
        directory = raw_directory.strip().strip('"')
        if not directory:
            continue
        for name in names:
            candidate = (Path(directory) / name).resolve()
            normalized = os.path.normcase(str(candidate))
            if normalized not in seen and candidate.is_file():
                seen.add(normalized)
                yield candidate


def locate_tool(environment_name, executable_name, required):
    configured = os.environ.get(environment_name, "").strip()
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.is_file() and works_after_copy(candidate):
            return candidate
        raise SystemExit(
            f"{environment_name} non indica un binario {executable_name} portabile valido: "
            f"{candidate}"
        )
    rejected = []
    for candidate in path_candidates(executable_name):
        if works_after_copy(candidate):
            return candidate
        rejected.append(str(candidate))
    if required:
        detail = f" Binari non portabili ignorati: {', '.join(rejected)}." if rejected else ""
        raise SystemExit(
            f"{executable_name} portabile non trovato nel PATH o in {environment_name}.{detail}"
        )
    return None


ffmpeg = locate_tool("ATS_FFMPEG_BINARY", "ffmpeg", True)
ffprobe = locate_tool("ATS_FFPROBE_BINARY", "ffprobe", True)
fpcalc = locate_tool("ATS_FPCALC_BINARY", "fpcalc", False)

datas = [
    (str(frontend), "frontend/dist"),
    (str(icon), "Icon"),
    (str(root / "README.md"), "."),
    (str(root / "THIRD_PARTY_NOTICES.md"), "."),
    (str(ffmpeg), "tools"),
    (str(ffprobe), "tools"),
]
if fpcalc:
    datas.append((str(fpcalc), "tools"))

ffmpeg_license = ffmpeg.parent.parent / "LICENSE"
if ffmpeg_license.is_file():
    datas.append((str(ffmpeg_license), "licenses"))

hiddenimports = ["webview.platforms.edgechromium", "webview.platforms.winforms"]

a = Analysis(
    [str(root / "desktop_main.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Audio Track Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon),
    version=str(root / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Audio Track Studio",
)
