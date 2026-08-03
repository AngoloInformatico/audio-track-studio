"""Windows-safe filename helpers."""

import re
from pathlib import Path
from string import Formatter

_INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
_TEMPLATE_FIELDS = {"track", "artist", "title"}


def safe_display_name(value: str) -> str:
    """Discard path components and replace Windows-invalid characters."""

    name = Path(value.replace("\\", "/")).name.strip()
    name = _INVALID_WINDOWS_CHARS.sub("_", name).rstrip(". ")
    if not name or name in {".", ".."}:
        raise ValueError("Nome file non valido.")
    return name


def render_track_filename(
    template: str,
    *,
    track: int,
    artist: str,
    title: str,
    extension: str = ".flac",
) -> str:
    """Render a constrained filename template and make it Windows-safe."""

    try:
        fields = {field_name for _, field_name, _, _ in Formatter().parse(template) if field_name}
    except ValueError as exc:
        raise ValueError("Schema nome file non valido.") from exc
    unsupported = fields - _TEMPLATE_FIELDS
    if unsupported:
        raise ValueError(f"Placeholder non supportato: {sorted(unsupported)[0]}.")
    try:
        rendered = template.format(
            track=track,
            artist=artist or "Artista sconosciuto",
            title=title or f"Traccia {track:02d}",
        )
    except (KeyError, ValueError) as exc:
        raise ValueError("Schema nome file non valido.") from exc

    normalized_extension = extension if extension.startswith(".") else f".{extension}"
    if rendered.lower().endswith(normalized_extension.lower()):
        rendered = rendered[: -len(normalized_extension)]
    filename = _INVALID_WINDOWS_CHARS.sub("_", rendered).strip().rstrip(". ")
    filename = re.sub(r"\s+", " ", filename)
    if not filename:
        raise ValueError("Lo schema produce un nome file vuoto.")
    if filename.split(".", maxsplit=1)[0].upper() in _RESERVED_WINDOWS_NAMES:
        filename = f"_{filename}"
    return f"{filename[:180].rstrip()}{normalized_extension.lower()}"
