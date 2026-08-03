"""Build, prepare, and restore portable Audio Track Studio projects."""

import base64
import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from time import monotonic
from uuid import uuid4

from backend.audio.library import AudioLibrary, AudioLibraryError, ImportedAudio
from backend.metadata.cover import CoverError, CoverStore
from backend.models.tracks import Track
from backend.projects.models import (
    ProjectApplyResult,
    ProjectCover,
    ProjectDocument,
    ProjectPreview,
    ProjectSettings,
    ProjectSource,
    ProjectSummary,
    ProjectTrack,
)
from backend.projects.storage import ProjectStorage
from backend.tracks.store import TrackStateNotFoundError, TrackStore, TrackStoreError


class ProjectError(RuntimeError):
    """Raised when a project cannot be built or restored safely."""


@dataclass(frozen=True, slots=True)
class _PreparedProject:
    document: ProjectDocument
    persisted_project_id: str | None
    created_at: float


class ProjectPreparationCache:
    """Short-lived in-memory handoff between project inspection and source relink."""

    _instance: "ProjectPreparationCache | None" = None
    _instance_lock = RLock()
    lifetime_seconds = 30 * 60

    def __init__(self) -> None:
        self._items: dict[str, _PreparedProject] = {}
        self._lock = RLock()

    @classmethod
    def instance(cls) -> "ProjectPreparationCache":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def put(self, document: ProjectDocument, persisted_project_id: str | None = None) -> str:
        token = uuid4().hex
        now = monotonic()
        with self._lock:
            self._items = {
                key: value
                for key, value in self._items.items()
                if now - value.created_at <= self.lifetime_seconds
            }
            self._items[token] = _PreparedProject(document, persisted_project_id, now)
            while len(self._items) > 20:
                self._items.pop(next(iter(self._items)))
        return token

    def get(self, token: str) -> _PreparedProject:
        with self._lock:
            item = self._items.get(token)
        if item is None or monotonic() - item.created_at > self.lifetime_seconds:
            raise ProjectError("L'anteprima del progetto è scaduta. Apri nuovamente il file.")
        return item

    def consume(self, token: str) -> None:
        with self._lock:
            self._items.pop(token, None)


class ProjectService:
    """Serialize editor state without ever copying the source audio into the project."""

    def __init__(self, storage: ProjectStorage | None = None) -> None:
        self.storage = storage or ProjectStorage()
        self.cache = ProjectPreparationCache.instance()

    def save(
        self,
        audio_id: str,
        name: str,
        project_id: str | None,
        save_as: bool,
        settings: ProjectSettings,
    ) -> tuple[ProjectSummary, Path]:
        existing = None if save_as or not project_id else self.storage.find_saved(project_id)
        previous, existing_path = existing if existing is not None else (None, None)
        document = self.build_document(
            audio_id,
            name,
            settings,
            project_id=previous.id if previous else uuid4().hex,
            created_at=previous.created_at if previous else None,
        )
        path = self.storage.save(document, existing_path)
        self.storage.remove_recovery(audio_id)
        return self.storage.summary(document), path

    def autosave(
        self,
        audio_id: str,
        name: str,
        project_id: str | None,
        settings: ProjectSettings,
    ) -> ProjectSummary:
        existing = self.storage.find_saved(project_id) if project_id else None
        previous = existing[0] if existing else None
        document = self.build_document(
            audio_id,
            name,
            settings,
            project_id=previous.id if previous else uuid4().hex,
            created_at=previous.created_at if previous else None,
        )
        self.storage.save_recovery(audio_id, document)
        return self.storage.summary(document, "recovery")

    def build_document(
        self,
        audio_id: str,
        name: str,
        settings: ProjectSettings,
        project_id: str,
        created_at: datetime | None = None,
    ) -> ProjectDocument:
        try:
            source = AudioLibrary.instance().get(audio_id)
            collection = TrackStore.instance().get(audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise ProjectError(str(exc)) from exc
        covers: dict[str, ProjectCover] = {}
        tracks: list[ProjectTrack] = []
        cover_store = CoverStore.instance()
        for track in collection.tracks:
            asset = cover_store.get_optional(audio_id, track.id)
            cover_key = None
            if asset is not None:
                data = asset.path.read_bytes()
                cover_key = hashlib.sha256(data).hexdigest()
                if cover_key not in covers:
                    covers[cover_key] = ProjectCover(
                        mime_type=asset.mime_type,
                        source=asset.source,
                        data_base64=base64.b64encode(data).decode("ascii"),
                    )
            values = track.model_dump(exclude={"cover"})
            tracks.append(ProjectTrack(**values, cover_key=cover_key))
        now = datetime.now(UTC)
        return ProjectDocument(
            id=project_id,
            name=name.strip(),
            created_at=created_at or now,
            updated_at=now,
            source=ProjectSource(
                name=source.original_name,
                size_bytes=source.path.stat().st_size,
                duration_seconds=collection.tracks[-1].end_seconds,
                format=source.path.suffix.lstrip(".").upper(),
                sha256=self._source_hash(source),
            ),
            markers=collection.markers,
            tracks=tracks,
            covers=covers,
            settings=settings,
        )

    def prepare(
        self, document: ProjectDocument, persisted_project_id: str | None = None
    ) -> ProjectPreview:
        self._validate_document(document)
        token = self.cache.put(document, persisted_project_id)
        return ProjectPreview(
            token=token,
            name=document.name,
            source=document.source,
            track_count=len(document.tracks),
            has_covers=bool(document.covers),
            settings=document.settings,
            persisted_project_id=persisted_project_id,
        )

    async def apply(self, token: str, audio_id: str) -> ProjectApplyResult:
        prepared = self.cache.get(token)
        document = prepared.document
        try:
            imported = AudioLibrary.instance().get(audio_id)
            current = TrackStore.instance().get(audio_id)
        except (AudioLibraryError, TrackStateNotFoundError) as exc:
            raise ProjectError(str(exc)) from exc
        actual_size = imported.path.stat().st_size
        actual_duration = current.tracks[-1].end_seconds
        wrong_size = actual_size != document.source.size_bytes
        wrong_duration = abs(actual_duration - document.source.duration_seconds) > 0.5
        wrong_hash = self._source_hash(imported) != document.source.sha256
        if wrong_size or wrong_duration or wrong_hash:
            raise ProjectError(
                "Il file selezionato non corrisponde alla sorgente del progetto. "
                "Scegli il file originale oppure una copia identica."
            )
        decoded_covers = self._decode_covers(document)
        restored_tracks = [
            Track(**track.model_dump(exclude={"cover_key"}), cover=None)
            for track in document.tracks
        ]
        try:
            collection = TrackStore.instance().restore(
                audio_id,
                actual_duration,
                document.markers,
                restored_tracks,
            )
            for project_track in document.tracks:
                if project_track.cover_key is None:
                    continue
                cover_data, source = decoded_covers[project_track.cover_key]
                cover = await CoverStore.instance().save_bytes(
                    audio_id,
                    project_track.id,
                    cover_data,
                    source,
                )
                collection = TrackStore.instance().set_cover(audio_id, project_track.id, cover)
        except (TrackStoreError, CoverError) as exc:
            raise ProjectError(str(exc)) from exc
        self.cache.consume(token)
        persisted_id = prepared.persisted_project_id
        summary = self.storage.summary(document)
        if persisted_id is None:
            summary.download_url = None
        return ProjectApplyResult(
            project=summary,
            persisted_project_id=persisted_id,
            markers=collection.markers,
            track_count=len(collection.tracks),
        )

    @staticmethod
    def _validate_document(document: ProjectDocument) -> None:
        points = [0.0, *document.markers, document.source.duration_seconds]
        if document.markers != sorted(document.markers):
            raise ProjectError("I marker del progetto non sono ordinati.")
        if len(document.tracks) != len(points) - 1:
            raise ProjectError("Il numero di tracce non corrisponde ai marker del progetto.")
        if len({track.id for track in document.tracks}) != len(document.tracks):
            raise ProjectError("Il progetto contiene identificatori traccia duplicati.")
        for index, (track, start, end) in enumerate(
            zip(document.tracks, points[:-1], points[1:], strict=True), start=1
        ):
            wrong_start = abs(track.start_seconds - start) > 0.5
            wrong_end = abs(track.end_seconds - end) > 0.5
            if track.number != index or wrong_start or wrong_end:
                raise ProjectError("La suddivisione delle tracce nel progetto non è coerente.")
            if track.cover_key is not None and track.cover_key not in document.covers:
                raise ProjectError("Il progetto fa riferimento a una copertina mancante.")

    @staticmethod
    def _decode_covers(document: ProjectDocument) -> dict[str, tuple[bytes, str]]:
        decoded: dict[str, tuple[bytes, str]] = {}
        for key, cover in document.covers.items():
            try:
                data = base64.b64decode(cover.data_base64, validate=True)
                mime_type, _ = CoverStore.detect_image(data)
            except (ValueError, CoverError) as exc:
                raise ProjectError("Una copertina incorporata nel progetto non è valida.") from exc
            if mime_type != cover.mime_type:
                raise ProjectError("Il tipo di una copertina del progetto non è coerente.")
            if hashlib.sha256(data).hexdigest() != key:
                raise ProjectError("L'integrità di una copertina del progetto non è verificabile.")
            decoded[key] = (data, cover.source)
        return decoded

    @staticmethod
    def _source_hash(source: ImportedAudio) -> str:
        known = source.sha256
        if known:
            return str(known)
        digest = hashlib.sha256()
        with source.path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        return digest.hexdigest()
