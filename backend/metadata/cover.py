"""Validated session-scoped cover artwork storage."""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from uuid import uuid4

from fastapi import UploadFile

from backend.audio.library import AudioLibrary, AudioLibraryError
from backend.models.tracks import CoverInfo


class CoverError(RuntimeError):
    """Raised when artwork is invalid or unavailable."""


@dataclass(frozen=True, slots=True)
class CoverAsset:
    path: Path
    mime_type: str
    size_bytes: int
    source: str


class CoverStore:
    """Keep cover files beside the managed audio copy and expose no local paths."""

    _instance: "CoverStore | None" = None
    _instance_lock = RLock()
    maximum_bytes = 10 * 1024 * 1024

    def __init__(self) -> None:
        self._assets: dict[tuple[str, str], CoverAsset] = {}
        self._source_assets: dict[str, CoverAsset] = {}
        self._source_opt_out: set[tuple[str, str]] = set()
        self._lock = RLock()

    @classmethod
    def instance(cls) -> "CoverStore":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def save_upload(self, audio_id: str, track_id: str, upload: UploadFile) -> CoverInfo:
        try:
            source = AudioLibrary.instance().get(audio_id)
        except AudioLibraryError as exc:
            raise CoverError(str(exc)) from exc
        directory = source.path.parent / "covers"
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        temporary = directory / f".{track_id}-{uuid4().hex}.upload"
        size = 0
        try:
            with temporary.open("xb") as destination:
                while chunk := await upload.read(256 * 1024):
                    size += len(chunk)
                    if size > self.maximum_bytes:
                        raise CoverError("La copertina supera il limite di 10 MB.")
                    await asyncio.to_thread(destination.write, chunk)
            if not size:
                raise CoverError("Il file della copertina è vuoto.")
            data = await asyncio.to_thread(temporary.read_bytes)
            mime_type, extension = self.detect_image(data)
            target = directory / f"{track_id}{extension}"
            await asyncio.to_thread(os.replace, temporary, target)
            return self._register(audio_id, track_id, target, mime_type, size, "manual")
        finally:
            await asyncio.to_thread(temporary.unlink, missing_ok=True)

    async def save_bytes(
        self,
        audio_id: str,
        track_id: str,
        data: bytes,
        source_name: str,
    ) -> CoverInfo:
        if not data:
            raise CoverError("La fonte non ha restituito una copertina.")
        if len(data) > self.maximum_bytes:
            raise CoverError("La copertina supera il limite di 10 MB.")
        mime_type, extension = self.detect_image(data)
        try:
            source = AudioLibrary.instance().get(audio_id)
        except AudioLibraryError as exc:
            raise CoverError(str(exc)) from exc
        directory = source.path.parent / "covers"
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        temporary = directory / f".{track_id}-{uuid4().hex}.download"
        target = directory / f"{track_id}{extension}"
        try:
            await asyncio.to_thread(temporary.write_bytes, data)
            await asyncio.to_thread(os.replace, temporary, target)
        finally:
            await asyncio.to_thread(temporary.unlink, missing_ok=True)
        return self._register(audio_id, track_id, target, mime_type, len(data), source_name)

    async def save_source(self, audio_id: str, data: bytes) -> CoverInfo:
        """Store one embedded source cover that can be shared by every track."""

        if not data:
            raise CoverError("Il file sorgente non contiene una copertina.")
        if len(data) > self.maximum_bytes:
            raise CoverError("La copertina sorgente supera il limite di 10 MB.")
        mime_type, extension = self.detect_image(data)
        try:
            source = AudioLibrary.instance().get(audio_id)
        except AudioLibraryError as exc:
            raise CoverError(str(exc)) from exc
        directory = source.path.parent / "covers"
        await asyncio.to_thread(directory.mkdir, parents=True, exist_ok=True)
        temporary = directory / f".source-{uuid4().hex}.embedded"
        target = directory / f"source-cover{extension}"
        try:
            await asyncio.to_thread(temporary.write_bytes, data)
            await asyncio.to_thread(os.replace, temporary, target)
        finally:
            await asyncio.to_thread(temporary.unlink, missing_ok=True)
        asset = CoverAsset(target, mime_type, len(data), "source")
        with self._lock:
            previous = self._source_assets.get(audio_id)
            self._source_assets[audio_id] = asset
        if previous is not None and previous.path != target:
            previous.path.unlink(missing_ok=True)
        return CoverInfo(
            url=f"/api/audio/{audio_id}/source-cover",
            mime_type=mime_type,
            size_bytes=len(data),
            source="source",
        )

    def get(self, audio_id: str, track_id: str) -> CoverAsset:
        key = (audio_id, track_id)
        with self._lock:
            asset = self._assets.get(key)
            if asset is None and key not in self._source_opt_out:
                asset = self._source_assets.get(audio_id)
        if asset is None or not asset.path.is_file():
            raise CoverError("Copertina non trovata o sessione scaduta.")
        return asset

    def get_optional(self, audio_id: str, track_id: str) -> CoverAsset | None:
        try:
            return self.get(audio_id, track_id)
        except CoverError:
            return None

    async def remove(self, audio_id: str, track_id: str) -> None:
        key = (audio_id, track_id)
        with self._lock:
            asset = self._assets.pop(key, None)
            inherited = self._source_assets.get(audio_id)
            if asset is not None or inherited is not None:
                self._source_opt_out.add(key)
        if asset is None and inherited is None:
            raise CoverError("Copertina non trovata o sessione scaduta.")
        if asset is not None:
            await asyncio.to_thread(asset.path.unlink, missing_ok=True)

    def remove_session(self, audio_id: str) -> None:
        with self._lock:
            keys = [key for key in self._assets if key[0] == audio_id]
            for key in keys:
                self._assets.pop(key, None)
            self._source_assets.pop(audio_id, None)
            self._source_opt_out = {
                key for key in self._source_opt_out if key[0] != audio_id
            }

    def _register(
        self,
        audio_id: str,
        track_id: str,
        path: Path,
        mime_type: str,
        size_bytes: int,
        source: str,
    ) -> CoverInfo:
        asset = CoverAsset(path, mime_type, size_bytes, source)
        with self._lock:
            key = (audio_id, track_id)
            previous = self._assets.get(key)
            self._assets[key] = asset
            self._source_opt_out.discard(key)
        if previous is not None and previous.path != path:
            previous.path.unlink(missing_ok=True)
        return CoverInfo(
            url=f"/api/audio/{audio_id}/tracks/{track_id}/cover",
            mime_type=mime_type,
            size_bytes=size_bytes,
            source=source,
        )

    @staticmethod
    def detect_image(data: bytes) -> tuple[str, str]:
        if data.startswith(b"\xff\xd8\xff") and data.endswith(b"\xff\xd9"):
            return "image/jpeg", ".jpg"
        if data.startswith(b"\x89PNG\r\n\x1a\n") and data.endswith(
            b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
        ):
            return "image/png", ".png"
        raise CoverError("Sono supportate soltanto copertine JPEG e PNG valide.")
