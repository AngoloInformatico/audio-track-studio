"""Windows desktop entry point backed by pywebview and the local FastAPI app."""

import ctypes
import json
import multiprocessing
import sys
import urllib.request
from pathlib import Path

from backend.core.config import get_settings
from backend.core.resources import resource_path
from desktop.server import DesktopServer


def run() -> int:
    multiprocessing.freeze_support()
    server: DesktopServer | None = None
    try:
        frontend = resource_path("frontend", "dist", "index.html")
        if not frontend.is_file():
            raise RuntimeError("Frontend non trovato. Esegui prima la build di produzione.")
        get_settings().ensure_directories()
        server = DesktopServer()
        server.start()

        import webview

        window = webview.create_window(
            "Audio Track Studio",
            server.url,
            width=1440,
            height=920,
            min_size=(1180, 700),
            resizable=True,
            background_color="#101315",
            text_select=False,
        )
        window.events.closed += lambda: server.stop()
        webview.start(
            gui="edgechromium",
            debug=False,
            private_mode=False,
            storage_path=str(get_settings().data_dir / "webview"),
        )
        return 0
    except Exception as exc:
        _show_fatal_error(str(exc))
        return 1
    finally:
        if server is not None:
            server.stop()


def run_smoke_test(report_path: Path | None = None) -> int:
    """Exercise the frozen frontend, API and bundled audio tools without opening a window."""

    server: DesktopServer | None = None
    report: dict[str, object]
    try:
        settings = get_settings()
        settings.ensure_directories()
        server = DesktopServer()
        server.start()
        with urllib.request.urlopen(server.url, timeout=10) as response:
            frontend = response.read().decode("utf-8")
        with urllib.request.urlopen(f"{server.url}/api/health", timeout=10) as response:
            health = json.loads(response.read().decode("utf-8"))
        if "Audio Track Studio" not in frontend:
            raise RuntimeError("Frontend incorporato non valido.")
        tools = health.get("tools", {})
        if health.get("status") != "ok" or not tools.get("ffmpeg", {}).get("available"):
            raise RuntimeError("FFmpeg incorporato non disponibile.")
        if not tools.get("ffprobe", {}).get("available"):
            raise RuntimeError("ffprobe incorporato non disponibile.")
        report = {
            "status": "ok",
            "frontend": True,
            "api": True,
            "ffmpeg": True,
            "ffprobe": True,
            "data_dir": str(settings.data_dir),
        }
        result = 0
    except Exception as exc:
        report = {"status": "error", "message": str(exc)}
        result = 1
    finally:
        if server is not None:
            server.stop()
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return result


def _show_fatal_error(message: str) -> None:
    detail = f"Audio Track Studio non può essere avviato.\n\n{message}"
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(None, detail, "Audio Track Studio", 0x10)
    else:
        print(detail, file=sys.stderr)


def icon_path() -> Path:
    """Expose the canonical icon location to packaging checks."""

    return resource_path("Icon", "icon.ico")
