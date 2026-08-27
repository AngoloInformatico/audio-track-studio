"""Centralized application settings."""

import json
import os
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from threading import Lock

from backend.core.resources import configured_tool

_CONFIG_LOCK = Lock()


def _default_data_dir() -> Path:
    configured = os.getenv("ATS_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    base = Path(os.getenv("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "AudioTrackStudio"


def _default_runtime_dir() -> Path:
    configured = os.getenv("ATS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(tempfile.gettempdir()) / "AudioTrackStudio"


def _default_export_dir() -> Path:
    configured = os.getenv("ATS_EXPORT_DIR")
    if configured:
        return Path(configured).expanduser()
    saved = _read_user_config().get("export_directory")
    if isinstance(saved, str) and saved.strip():
        return Path(saved).expanduser()
    return Path.home() / "Music" / "Audio Track Studio"


def _default_acoustid_key() -> str:
    configured = os.getenv("ACOUSTID_API_KEY", "").strip()
    if configured:
        return configured
    saved = _read_user_config().get("acoustid_api_key")
    return saved.strip() if isinstance(saved, str) else ""


def _default_fpcalc_binary() -> str:
    configured = os.getenv("ATS_FPCALC_BINARY", "").strip()
    if configured:
        return str(Path(configured).expanduser())
    saved = _read_user_config().get("fpcalc_path")
    if isinstance(saved, str) and saved.strip():
        return str(Path(saved).expanduser())
    return configured_tool("ATS_FPCALC_BINARY", "fpcalc")


def _read_user_config() -> dict[str, object]:
    path = _default_data_dir() / "config.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def update_user_config(updates: dict[str, object]) -> None:
    """Merge user settings and replace config.json atomically."""

    path = _default_data_dir() / "config.json"
    with _CONFIG_LOCK:
        payload = _read_user_config()
        payload.update(updates)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    get_settings.cache_clear()


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Audio Track Studio"
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8765
    ffmpeg_binary: str = field(
        default_factory=lambda: configured_tool("ATS_FFMPEG_BINARY", "ffmpeg")
    )
    ffprobe_binary: str = field(
        default_factory=lambda: configured_tool("ATS_FFPROBE_BINARY", "ffprobe")
    )
    fpcalc_binary: str = field(
        default_factory=_default_fpcalc_binary
    )
    acoustid_api_key: str = field(default_factory=_default_acoustid_key)
    acoustid_lookup_url: str = "https://api.acoustid.org/v2/lookup"
    recognition_timeout_seconds: int = 45
    ffprobe_timeout_seconds: int = 60
    upload_chunk_bytes: int = 1024 * 1024
    data_dir: Path = field(default_factory=_default_data_dir)
    runtime_dir: Path = field(default_factory=_default_runtime_dir)
    default_export_dir: Path = field(default_factory=_default_export_dir)
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:5173", "http://localhost:5173")
    supported_extensions: frozenset[str] = frozenset({".flac", ".wav", ".mp3", ".m4a", ".aac"})

    @property
    def cache_dir(self) -> Path:
        return self.runtime_dir / "cache"

    @property
    def webview_dir(self) -> Path:
        return self.runtime_dir / "webview"

    @property
    def log_dir(self) -> Path:
        return self.data_dir / "logs"

    @property
    def project_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def recovery_dir(self) -> Path:
        return self.data_dir / "recovery"

    @property
    def config_file(self) -> Path:
        return self.data_dir / "config.json"

    def ensure_directories(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            temporary = self.config_file.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(
                    {"acoustid_api_key": "", "fpcalc_path": "", "export_directory": ""},
                    indent=2,
                ),
                encoding="utf-8",
            )
            os.replace(temporary, self.config_file)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
