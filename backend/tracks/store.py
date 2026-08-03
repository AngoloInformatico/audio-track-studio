"""Thread-safe in-memory editor state for imported audio sessions."""

import math
from dataclasses import dataclass, replace
from threading import RLock
from uuid import uuid4

from backend.models.recognition import RecognitionMetadataItem
from backend.models.tracks import CoverInfo, Track, TrackCollection, TrackMetadataUpdate

MIN_TRACK_SECONDS = 0.05


class TrackStoreError(RuntimeError):
    """Raised for invalid boundary operations."""


class TrackStateNotFoundError(TrackStoreError):
    """Raised when an editor session or track no longer exists."""


@dataclass(slots=True)
class _TrackState:
    id: str
    start_seconds: float
    end_seconds: float
    artist: str = ""
    title: str = ""
    album: str = ""
    album_artist: str = ""
    track_number: int | None = None
    disc_number: int | None = None
    date: str = ""
    genre: str = ""
    comment: str = ""
    composer: str = ""
    release_group_id: str | None = None
    recognition_provider: str | None = None
    recognition_external_id: str | None = None
    recognition_recording_id: str | None = None
    recognition_confidence: float | None = None
    cover: CoverInfo | None = None


@dataclass(slots=True)
class _SessionState:
    duration_seconds: float
    markers: list[float]
    tracks: list[_TrackState]
    default_artist: str = ""
    source_cover: CoverInfo | None = None


class TrackStore:
    """Keep marker changes atomic so every consumer sees valid segments."""

    _instance: "TrackStore | None" = None
    _instance_lock = RLock()

    def __init__(self) -> None:
        self._sessions: dict[str, _SessionState] = {}
        self._lock = RLock()

    @classmethod
    def instance(cls) -> "TrackStore":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def initialize(
        self,
        audio_id: str,
        duration_seconds: float,
        *,
        default_artist: str = "",
        source_cover: CoverInfo | None = None,
    ) -> TrackCollection:
        duration = round(float(duration_seconds), 3)
        if not math.isfinite(duration) or duration <= 0:
            raise TrackStoreError("La durata dell'audio non è valida.")
        fallback_artist = default_artist.strip()[:300]
        state = _SessionState(
            duration,
            [],
            [self._new_track(0.0, duration, audio_id, fallback_artist, source_cover)],
            fallback_artist,
            source_cover,
        )
        with self._lock:
            self._sessions[audio_id] = state
        return self._serialize(state)

    def get(self, audio_id: str) -> TrackCollection:
        with self._lock:
            state = self._require_session(audio_id)
            return self._serialize(state)

    def replace_markers(self, audio_id: str, markers: list[float]) -> TrackCollection:
        with self._lock:
            state = self._require_session(audio_id)
            cleaned = self._validate_markers(markers, state.duration_seconds)
            intervals = self._intervals(cleaned, state.duration_seconds)
            state.tracks = self._remap_tracks(audio_id, state, intervals)
            state.markers = cleaned
            return self._serialize(state)

    def update_metadata(self, audio_id: str, track_id: str, artist: str, title: str) -> TrackCollection:
        return self.patch_metadata(
            audio_id,
            track_id,
            TrackMetadataUpdate(artist=artist, title=title),
        )

    def patch_metadata(
        self, audio_id: str, track_id: str, update: TrackMetadataUpdate
    ) -> TrackCollection:
        with self._lock:
            state = self._require_session(audio_id)
            track = next((item for item in state.tracks if item.id == track_id), None)
            if track is None:
                raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
            values = update.model_dump(exclude_unset=True)
            for field_name, value in values.items():
                setattr(track, field_name, value)
            return self._serialize(state)

    def set_cover(self, audio_id: str, track_id: str, cover: CoverInfo | None) -> TrackCollection:
        with self._lock:
            state = self._require_session(audio_id)
            track = next((item for item in state.tracks if item.id == track_id), None)
            if track is None:
                raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
            track.cover = cover
            return self._serialize(state)

    def restore(
        self,
        audio_id: str,
        duration_seconds: float,
        markers: list[float],
        tracks: list[Track],
    ) -> TrackCollection:
        """Replace a fresh editor session with a validated project snapshot."""

        duration = round(float(duration_seconds), 3)
        cleaned = self._validate_markers(markers, duration)
        intervals = self._intervals(cleaned, duration)
        if len(tracks) != len(intervals):
            raise TrackStoreError("Il progetto non contiene una suddivisione coerente.")
        if len({track.id for track in tracks}) != len(tracks):
            raise TrackStoreError("Il progetto contiene identificatori traccia duplicati.")
        with self._lock:
            previous = self._sessions.get(audio_id)
            default_artist = previous.default_artist if previous else ""
            source_cover = previous.source_cover if previous else None
        restored: list[_TrackState] = []
        for index, (track, (start, end)) in enumerate(zip(tracks, intervals, strict=True), start=1):
            if track.number != index:
                raise TrackStoreError("La numerazione delle tracce del progetto non è coerente.")
            if abs(track.start_seconds - start) > 0.5 or abs(track.end_seconds - end) > 0.5:
                raise TrackStoreError("I timestamp del progetto non corrispondono ai marker.")
            inherited_cover = self._cover_for_track(audio_id, track.id, source_cover)
            restored.append(
                _TrackState(
                    id=track.id,
                    start_seconds=start,
                    end_seconds=end,
                    artist=track.artist or default_artist,
                    title=track.title,
                    album=track.album,
                    album_artist=track.album_artist,
                    track_number=track.track_number,
                    disc_number=track.disc_number,
                    date=track.date,
                    genre=track.genre,
                    comment=track.comment,
                    composer=track.composer,
                    release_group_id=track.release_group_id,
                    recognition_provider=track.recognition_provider,
                    recognition_external_id=track.recognition_external_id,
                    recognition_recording_id=track.recognition_recording_id,
                    recognition_confidence=track.recognition_confidence,
                    cover=track.cover or inherited_cover,
                )
            )
        state = _SessionState(duration, cleaned, restored, default_artist, source_cover)
        with self._lock:
            self._sessions[audio_id] = state
            return self._serialize(state)

    def update_metadata_batch(
        self, audio_id: str, items: list[RecognitionMetadataItem]
    ) -> TrackCollection:
        """Validate every target before applying recognition choices atomically."""

        with self._lock:
            state = self._require_session(audio_id)
            by_id = {track.id: track for track in state.tracks}
            if len({item.track_id for item in items}) != len(items):
                raise TrackStoreError("Una traccia compare più volte nell'aggiornamento.")
            unknown = next((item.track_id for item in items if item.track_id not in by_id), None)
            if unknown:
                raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
            for item in items:
                track = by_id[item.track_id]
                track.artist = item.artist.strip()
                track.title = item.title.strip()
                if item.album is not None:
                    track.album = item.album.strip()
                if item.date is not None:
                    track.date = item.date.strip()
                if item.release_group_id is not None:
                    track.release_group_id = item.release_group_id
                if item.provider is not None:
                    track.recognition_provider = item.provider
                if item.external_id is not None:
                    track.recognition_external_id = item.external_id
                if item.recording_id is not None:
                    track.recognition_recording_id = item.recording_id
                if item.confidence is not None:
                    track.recognition_confidence = item.confidence
            return self._serialize(state)

    def remove(self, audio_id: str) -> None:
        with self._lock:
            self._sessions.pop(audio_id, None)

    def _require_session(self, audio_id: str) -> _SessionState:
        state = self._sessions.get(audio_id)
        if state is None:
            raise TrackStateNotFoundError("Editor non trovato o sessione scaduta.")
        return state

    @staticmethod
    def _validate_markers(markers: list[float], duration: float) -> list[float]:
        cleaned: list[float] = []
        for marker in markers:
            value = round(float(marker), 3)
            if not math.isfinite(value):
                raise TrackStoreError("Un timestamp non è valido.")
            cleaned.append(value)
        if cleaned != sorted(cleaned):
            raise TrackStoreError("I marker devono essere ordinati.")
        points = [0.0, *cleaned, duration]
        if any(point <= 0 or point >= duration for point in cleaned):
            raise TrackStoreError("I marker devono trovarsi all'interno della durata dell'audio.")
        if any(end - start < MIN_TRACK_SECONDS for start, end in zip(points, points[1:], strict=False)):
            raise TrackStoreError("Ogni traccia deve durare almeno 50 millisecondi.")
        return cleaned

    @staticmethod
    def _intervals(markers: list[float], duration: float) -> list[tuple[float, float]]:
        points = [0.0, *markers, duration]
        return list(zip(points, points[1:], strict=False))

    def _remap_tracks(
        self,
        audio_id: str,
        state: _SessionState,
        intervals: list[tuple[float, float]],
    ) -> list[_TrackState]:
        available = list(state.tracks)
        remapped: list[_TrackState] = []
        for start, end in intervals:
            matching = max(
                available,
                key=lambda item: self._overlap(start, end, item.start_seconds, item.end_seconds),
                default=None,
            )
            overlap = (
                self._overlap(start, end, matching.start_seconds, matching.end_seconds) if matching else 0.0
            )
            if matching is not None and overlap > 0:
                available.remove(matching)
                remapped.append(replace(matching, start_seconds=start, end_seconds=end))
            else:
                remapped.append(
                    self._new_track(
                        start,
                        end,
                        audio_id,
                        state.default_artist,
                        state.source_cover,
                    )
                )
        return remapped

    @staticmethod
    def _overlap(start_a: float, end_a: float, start_b: float, end_b: float) -> float:
        return max(0.0, min(end_a, end_b) - max(start_a, start_b))

    @classmethod
    def _new_track(
        cls,
        start: float,
        end: float,
        audio_id: str,
        default_artist: str,
        source_cover: CoverInfo | None,
    ) -> _TrackState:
        track_id = uuid4().hex
        return _TrackState(
            track_id,
            start,
            end,
            artist=default_artist,
            cover=cls._cover_for_track(audio_id, track_id, source_cover),
        )

    @staticmethod
    def _cover_for_track(
        audio_id: str,
        track_id: str,
        source_cover: CoverInfo | None,
    ) -> CoverInfo | None:
        if source_cover is None:
            return None
        return source_cover.model_copy(
            update={"url": f"/api/audio/{audio_id}/tracks/{track_id}/cover"}
        )

    @staticmethod
    def _serialize(state: _SessionState) -> TrackCollection:
        return TrackCollection(
            markers=list(state.markers),
            tracks=[
                Track(
                    id=track.id,
                    number=index,
                    start_seconds=track.start_seconds,
                    end_seconds=track.end_seconds,
                    artist=track.artist,
                    title=track.title,
                    album=track.album,
                    album_artist=track.album_artist,
                    track_number=track.track_number or index,
                    disc_number=track.disc_number,
                    date=track.date,
                    genre=track.genre,
                    comment=track.comment,
                    composer=track.composer,
                    release_group_id=track.release_group_id,
                    recognition_provider=track.recognition_provider,
                    recognition_external_id=track.recognition_external_id,
                    recognition_recording_id=track.recognition_recording_id,
                    recognition_confidence=track.recognition_confidence,
                    cover=track.cover,
                )
                for index, track in enumerate(state.tracks, start=1)
            ],
        )
