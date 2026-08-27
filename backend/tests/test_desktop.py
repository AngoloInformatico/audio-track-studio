import urllib.request
from pathlib import Path

from backend.core import resources
from backend.core.config import Settings
from desktop.launcher import run_smoke_test
from desktop.server import DesktopServer


def test_configured_tool_prefers_packaged_binary(monkeypatch, tmp_path: Path) -> None:
    executable = tmp_path / "tools" / "ffmpeg.exe"
    executable.parent.mkdir()
    executable.write_bytes(b"tool")
    monkeypatch.delenv("ATS_FFMPEG_BINARY", raising=False)
    monkeypatch.setattr(resources, "application_root", lambda: tmp_path)

    assert resources.configured_tool("ATS_FFMPEG_BINARY", "ffmpeg") == str(executable)


def test_configured_tool_keeps_explicit_override(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "custom-ffmpeg.exe"
    monkeypatch.setenv("ATS_FFMPEG_BINARY", str(configured))

    assert resources.configured_tool("ATS_FFMPEG_BINARY", "ffmpeg") == str(configured)


def test_embedded_server_uses_loopback_and_serves_frontend() -> None:
    server = DesktopServer()
    try:
        server.start()
        assert server.url.startswith("http://127.0.0.1:")
        with urllib.request.urlopen(server.url, timeout=5) as response:
            page = response.read().decode("utf-8")
        assert response.status == 200
        assert "Audio Track Studio" in page
    finally:
        server.stop()


def test_source_smoke_test_writes_a_success_report(tmp_path: Path) -> None:
    report = tmp_path / "smoke.json"

    assert run_smoke_test(report) == 0
    assert '"status": "ok"' in report.read_text(encoding="utf-8")


def test_first_start_creates_default_user_configuration(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        runtime_dir=tmp_path / "runtime",
        default_export_dir=tmp_path / "exports",
    )

    settings.ensure_directories()

    assert settings.config_file.is_file()
    assert '"acoustid_api_key": ""' in settings.config_file.read_text(encoding="utf-8")
    assert '"fpcalc_path": ""' in settings.config_file.read_text(encoding="utf-8")
    assert settings.cache_dir == tmp_path / "runtime" / "cache"
