# -*- mode: python ; coding: utf-8 -*-

import os
import shutil
from pathlib import Path

root = Path(SPEC).resolve().parent.parent
frontend = root / "frontend" / "dist"
icon = root / "Icon" / "icon.ico"

if not (frontend / "index.html").is_file():
    raise SystemExit("Frontend non compilato: esegui npm run build.")
if not icon.is_file():
    raise SystemExit("Icon/icon.ico non trovato.")


def locate_tool(environment_name, executable_name, required):
    configured = os.environ.get(environment_name, "").strip()
    found = configured or shutil.which(executable_name)
    if required and not found:
        raise SystemExit(f"{executable_name} non trovato nel PATH o in {environment_name}.")
    return Path(found).resolve() if found else None


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
