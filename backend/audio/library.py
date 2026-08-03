"""Managed local working copies for browser-based development mode."""

import asyncio
import hashlib
import mimetypes
import shutil
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from uuid import uuid4

from fastapi import UploadFile

from backend.core.config import get_settings
from backend.metadata.filenames import safe_display_name


class AudioLibraryError(RuntimeError):
    """Raised for invalid or unavailable imported audio items."""


@dataclass(frozen=True, slots=True)
class ImportedAudio:
    id: str
    path: Path
    original_name: str
    media_type: str
    sha256: str = ""


class AudioLibrary:
    """Track temporary copies created by the web development workflow."""

    _instance: "AudioLibrary | None" = None
    _instance_lock = RLock()

    def __init__(self) -> None:
        self._items: dict[str, ImportedAudio] = {}
        self._lock = RLock()

    @classmethod
    def instance(cls) -> "AudioLibrary":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def import_upload(self, upload: UploadFile) -> ImportedAudio:
        """Stream an uploaded file to a dedicated cache directory."""

        settings = get_settings()
        try:
            original_name = safe_display_name(upload.filename or "audio")
        except ValueError as exc:
            raise AudioLibraryError(str(exc)) from exc
        extension = Path(original_name).suffix.lower()
        if extension not in settings.supported_extensions:
            supported = ", ".join(sorted(settings.supported_extensions))
            raise AudioLibraryError(f"Formato non supportato. Formati disponibili: {supported}.")

        audio_id = uuid4().hex
        target_dir = settings.cache_dir / audio_id
        target_path = target_dir / f"source{extension}"
        await asyncio.to_thread(target_dir.mkdir, parents=True, exist_ok=False)
        digest = hashlib.sha256()
        try:
            with target_path.open("xb") as destination:
                while chunk := await upload.read(settings.upload_chunk_bytes):
                    await asyncio.to_thread(destination.write, chunk)
                    digest.update(chunk)
            if target_path.stat().st_size == 0:
                raise AudioLibraryError("Il file selezionato è vuoto.")
        except Exception:
            await asyncio.to_thread(shutil.rmtree, target_dir, True)
            raise

        media_type = (
            upload.content_type or mimetypes.guess_type(original_name)[0] or "application/octet-stream"
        )
        item = ImportedAudio(audio_id, target_path, original_name, media_type, digest.hexdigest())
        with self._lock:
            self._items[audio_id] = item
        return item

    def get(self, audio_id: str) -> ImportedAudio:
        with self._lock:
            item = self._items.get(audio_id)
        if item is None or not item.path.is_file():
            raise AudioLibraryError("Audio non trovato o sessione scaduta.")
        return item

    async def remove(self, audio_id: str) -> None:
        with self._lock:
            item = self._items.pop(audio_id, None)
        if item is None:
            raise AudioLibraryError("Audio non trovato o sessione scaduta.")
        await asyncio.to_thread(shutil.rmtree, item.path.parent, True)
