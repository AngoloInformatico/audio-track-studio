"""Read reusable metadata and embedded artwork from an imported source."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile
from mutagen import MutagenError
from mutagen.flac import Picture


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    """Safe fallbacks extracted from the original audio file."""

    title: str
    artist: str
    cover_data: bytes | None = None


def read_source_metadata(path: Path, original_name: str) -> SourceMetadata:
    """Read tags without ever making audio import depend on their validity."""

    filename_title = Path(original_name).stem.strip()[:300] or "Audio sorgente"
    try:
        audio = MutagenFile(path)
    except (OSError, TypeError, ValueError, MutagenError):
        audio = None
    if audio is None:
        return SourceMetadata(filename_title, filename_title)
    return _metadata_from_mutagen(audio, filename_title)


def _metadata_from_mutagen(audio: Any, filename_title: str) -> SourceMetadata:
    tags = getattr(audio, "tags", None)
    title = _first_tag(tags, ("title", "TIT2", "\xa9nam")) or filename_title
    artist = _first_tag(tags, ("artist", "TPE1", "\xa9ART", "aART")) or title
    return SourceMetadata(title[:300], artist[:300], _embedded_cover(audio, tags))


def _first_tag(tags: Any, keys: tuple[str, ...]) -> str:
    if tags is None:
        return ""
    for key in keys:
        try:
            value = tags.get(key)
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        text = _tag_text(value)
        if text:
            return text
    return ""


def _tag_text(value: Any) -> str:
    if value is None:
        return ""
    value = getattr(value, "text", value)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else ""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value).strip()


def _embedded_cover(audio: Any, tags: Any) -> bytes | None:
    pictures = list(getattr(audio, "pictures", None) or [])
    if pictures:
        front = next((picture for picture in pictures if getattr(picture, "type", None) == 3), pictures[0])
        data = bytes(getattr(front, "data", b""))
        if data:
            return data

    if tags is None:
        return None
    getall = getattr(tags, "getall", None)
    if callable(getall):
        for key in ("APIC", "PIC"):
            frames = getall(key)
            if frames:
                data = bytes(getattr(frames[0], "data", b""))
                if data:
                    return data

    for key in ("covr", "coverart"):
        try:
            values = tags.get(key)
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        value = values[0] if isinstance(values, (list, tuple)) and values else values
        if value:
            data = bytes(value) if not isinstance(value, str) else value.encode("ascii", errors="ignore")
            if data.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")):
                return data
            try:
                decoded = base64.b64decode(data, validate=True)
            except ValueError:
                continue
            if decoded:
                return decoded

    try:
        blocks = tags.get("metadata_block_picture")
    except (AttributeError, KeyError, TypeError, ValueError):
        blocks = None
    block = blocks[0] if isinstance(blocks, (list, tuple)) and blocks else blocks
    if block:
        try:
            picture = Picture(base64.b64decode(block, validate=True))
        except (TypeError, ValueError, MutagenError):
            return None
        return bytes(picture.data) or None
    return None
