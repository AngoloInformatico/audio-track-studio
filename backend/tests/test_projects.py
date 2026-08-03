import asyncio
from pathlib import Path

import pytest

from backend.audio.library import AudioLibrary, ImportedAudio
from backend.core.config import Settings
from backend.metadata.cover import CoverStore
from backend.models.recognition import RecognitionMetadataItem
from backend.models.tracks import TrackMetadataUpdate
from backend.projects.models import ProjectSettings
from backend.projects.service import ProjectError, ProjectService
from backend.projects.storage import ProjectStorage, ProjectStorageError
from backend.tracks.store import TrackStore

JPEG_BYTES = b"\xff\xd8\xff\xe0project-cover\xff\xd9"


def test_project_roundtrip_restores_markers_metadata_recognition_and_cover(
    monkeypatch, tmp_path: Path
) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"same audio bytes")
    relocated = tmp_path / "moved-source.wav"
    relocated.write_bytes(source.read_bytes())
    items = {
        "source-audio": ImportedAudio("source-audio", source, "mix.wav", "audio/wav"),
        "restored-audio": ImportedAudio(
            "restored-audio", relocated, "moved-source.wav", "audio/wav"
        ),
    }
    monkeypatch.setattr(AudioLibrary.instance(), "get", lambda audio_id: items[audio_id])
    tracks = TrackStore.instance()
    covers = CoverStore.instance()
    tracks.initialize("source-audio", 60.0)
    split = tracks.replace_markers("source-audio", [30.0])
    first_id = split.tracks[0].id
    tracks.patch_metadata(
        "source-audio",
        first_id,
        TrackMetadataUpdate(
            artist="Artist",
            title="Title",
            album="Album",
            track_number=3,
            genre="Rock",
        ),
    )
    tracks.update_metadata_batch(
        "source-audio",
        [
            RecognitionMetadataItem(
                track_id=first_id,
                artist="Artist",
                title="Title",
                provider="acoustid",
                external_id="result-id",
                recording_id="recording-id",
                confidence=0.91,
            )
        ],
    )
    cover = asyncio.run(covers.save_bytes("source-audio", first_id, JPEG_BYTES, "manual"))
    tracks.set_cover("source-audio", first_id, cover)
    settings = Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "export")
    service = ProjectService(ProjectStorage(settings))
    try:
        summary, path = service.save(
            "source-audio",
            "Roundtrip",
            None,
            False,
            ProjectSettings(theme="dark", autosave_enabled=True),
        )
        document = service.storage.load_path(path)

        assert summary.name == "Roundtrip"
        assert str(source) not in path.read_text(encoding="utf-8")
        assert document.source.name == "mix.wav"
        assert len(document.covers) == 1
        assert service.storage.list_saved()[0][0].id == document.id

        preview = service.prepare(document, document.id)
        tracks.initialize("restored-audio", 60.0)
        applied = asyncio.run(service.apply(preview.token, "restored-audio"))
        restored = tracks.get("restored-audio")

        assert applied.persisted_project_id == document.id
        assert restored.markers == [30.0]
        assert restored.tracks[0].artist == "Artist"
        assert restored.tracks[0].album == "Album"
        assert restored.tracks[0].track_number == 3
        assert restored.tracks[0].recognition_provider == "acoustid"
        assert restored.tracks[0].recognition_external_id == "result-id"
        assert restored.tracks[0].recognition_recording_id == "recording-id"
        assert restored.tracks[0].recognition_confidence == 0.91
        assert restored.tracks[0].cover is not None
        assert covers.get("restored-audio", first_id).path.read_bytes() == JPEG_BYTES
    finally:
        tracks.remove("source-audio")
        tracks.remove("restored-audio")
        covers.remove_session("source-audio")
        covers.remove_session("restored-audio")


def test_project_relink_rejects_a_different_source(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"original")
    different = tmp_path / "different.wav"
    different.write_bytes(b"changed!")
    items = {
        "original": ImportedAudio("original", source, "source.wav", "audio/wav"),
        "different": ImportedAudio("different", different, "different.wav", "audio/wav"),
    }
    monkeypatch.setattr(AudioLibrary.instance(), "get", lambda audio_id: items[audio_id])
    tracks = TrackStore.instance()
    tracks.initialize("original", 10.0)
    tracks.initialize("different", 10.0)
    service = ProjectService(
        ProjectStorage(Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "out"))
    )
    try:
        document = service.build_document(
            "original",
            "Mismatch",
            ProjectSettings(),
            "project-id",
        )
        preview = service.prepare(document)

        with pytest.raises(ProjectError, match="non corrisponde"):
            asyncio.run(service.apply(preview.token, "different"))
    finally:
        tracks.remove("original")
        tracks.remove("different")


def test_invalid_project_schema_is_rejected(tmp_path: Path) -> None:
    storage = ProjectStorage(
        Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "out")
    )

    with pytest.raises(ProjectStorageError, match="non è valido"):
        storage.load_bytes(b'{"schema_name":"other","schema_version":99}')


def test_atomic_save_rejects_projects_over_the_limit(monkeypatch, tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    source.write_bytes(b"audio")
    monkeypatch.setattr(
        AudioLibrary.instance(),
        "get",
        lambda _audio_id: ImportedAudio("audio", source, "source.wav", "audio/wav"),
    )
    tracks = TrackStore.instance()
    tracks.initialize("audio", 5.0)
    storage = ProjectStorage(
        Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "out")
    )
    storage.maximum_project_bytes = 1
    try:
        with pytest.raises(ProjectStorageError, match="64 MB"):
            ProjectService(storage).save(
                "audio", "Too large", None, False, ProjectSettings()
            )
        assert not list(storage.settings.project_dir.glob("*.tmp"))
        assert not list(storage.settings.project_dir.glob("*.atsproject"))
    finally:
        tracks.remove("audio")
