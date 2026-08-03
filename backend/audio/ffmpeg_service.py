"""Centralized, shell-free access to ffmpeg and ffprobe."""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.models.audio import AudioInfo
from backend.models.health import ToolStatus


class FFmpegError(RuntimeError):
    """Raised when an FFmpeg operation cannot be completed safely."""


class FFmpegService:
    """Inspect and invoke the configured FFmpeg executables."""

    async def inspect_tools(self) -> dict[str, ToolStatus]:
        """Check both multimedia executables concurrently."""

        settings = get_settings()
        ffmpeg, ffprobe = await asyncio.gather(
            self._inspect_tool(settings.ffmpeg_binary),
            self._inspect_tool(settings.ffprobe_binary),
        )
        return {"ffmpeg": ffmpeg, "ffprobe": ffprobe}

    async def probe(self, path: Path, original_name: str | None = None) -> AudioInfo:
        """Read technical media information with ffprobe."""

        settings = get_settings()
        command = [
            settings.ffprobe_binary,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=settings.ffprobe_timeout_seconds,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except FileNotFoundError as exc:
            raise FFmpegError("ffprobe non è disponibile. Configuralo prima di aprire un audio.") from exc
        except subprocess.TimeoutExpired as exc:
            raise FFmpegError("ffprobe non ha risposto entro il tempo previsto.") from exc

        if result.returncode != 0:
            detail = result.stderr.strip() or "il file non può essere analizzato"
            raise FFmpegError(f"Impossibile leggere il file audio: {detail}")
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise FFmpegError("ffprobe ha restituito dati non validi.") from exc
        return parse_probe_payload(payload, path, original_name)

    async def _inspect_tool(self, binary: str) -> ToolStatus:
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                [binary, "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ToolStatus(available=False)
        first_line = result.stdout.splitlines()[0] if result.stdout else None
        return ToolStatus(available=result.returncode == 0, version=first_line)


def parse_probe_payload(payload: dict[str, Any], path: Path, original_name: str | None = None) -> AudioInfo:
    """Convert raw ffprobe JSON into the stable API model."""

    streams = payload.get("streams") or []
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    if audio_stream is None:
        raise FFmpegError("Il file selezionato non contiene una traccia audio.")

    format_data = payload.get("format") or {}
    duration = _to_float(audio_stream.get("duration")) or _to_float(format_data.get("duration")) or 0.0
    bitrate = _to_int(audio_stream.get("bit_rate")) or _to_int(format_data.get("bit_rate"))
    bit_depth = _positive_int(audio_stream.get("bits_per_raw_sample")) or _positive_int(
        audio_stream.get("bits_per_sample")
    )
    return AudioInfo(
        name=original_name or path.name,
        format=(format_data.get("format_name") or path.suffix.lstrip(".")).split(",")[0].upper(),
        codec=audio_stream.get("codec_name"),
        duration_seconds=duration,
        sample_rate=_to_int(audio_stream.get("sample_rate")),
        bit_depth=bit_depth,
        channels=_to_int(audio_stream.get("channels")),
        channel_layout=audio_stream.get("channel_layout"),
        bitrate=bitrate,
        size_bytes=_to_int(format_data.get("size")) or path.stat().st_size,
    )


def _to_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _positive_int(value: Any) -> int | None:
    parsed = _to_int(value)
    return parsed if parsed and parsed > 0 else None


def _to_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
