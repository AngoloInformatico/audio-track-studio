import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest
from mutagen.flac import FLAC

from backend.audio.library import AudioLibrary, ImportedAudio
from backend.export.service import ExportService
from backend.metadata.cover import CoverAsset, CoverError, CoverStore
from backend.models.tracks import Track, TrackMetadataUpdate
from backend.tracks.store import TrackStore

JPEG_BYTES = b"\xff\xd8\xff\xe0test-cover\xff\xd9"


def test_advanced_metadata_survives_boundary_changes() -> None:
    store = TrackStore()
    initial = store.initialize("metadata-audio", 90.0)
    updated = store.patch_metadata(
        "metadata-audio",
        initial.tracks[0].id,
        TrackMetadataUpdate(
            title="Song",
            artist="Artist",
            album="Album",
            album_artist="Album Artist",
            track_number=7,
            disc_number=2,
            date="2026-08-02",
            genre="Electronic",
            comment="Live version",
            composer="Composer",
        ),
    )

    split = store.replace_markers("metadata-audio", [45.0])

    assert split.tracks[0].id == updated.tracks[0].id
    assert split.tracks[0].album == "Album"
    assert split.tracks[0].album_artist == "Album Artist"
    assert split.tracks[0].track_number == 7
    assert split.tracks[0].disc_number == 2
    assert split.tracks[0].genre == "Electronic"
    assert split.tracks[0].composer == "Composer"


def test_cover_store_validates_and_keeps_paths_private(monkeypatch, tmp_path: Path) -> None:
    audio_id = "cover-audio"
    track_id = "track-id"
    source = tmp_path / "source.wav"
    source.touch()
    imported = ImportedAudio(audio_id, source, source.name, "audio/wav")
    monkeypatch.setattr(AudioLibrary.instance(), "get", lambda _: imported)
    store = CoverStore()

    info = asyncio.run(store.save_bytes(audio_id, track_id, JPEG_BYTES, "manual"))

    assert info.mime_type == "image/jpeg"
    assert info.url == f"/api/audio/{audio_id}/tracks/{track_id}/cover"
    assert str(tmp_path) not in info.model_dump_json()
    assert store.get(audio_id, track_id).path.read_bytes() == JPEG_BYTES

    with pytest.raises(CoverError, match="JPEG e PNG"):
        asyncio.run(store.save_bytes(audio_id, "bad", b"not an image", "manual"))


def test_source_cover_is_shared_and_can_be_overridden_or_removed(
    monkeypatch, tmp_path: Path
) -> None:
    audio_id = "source-cover-audio"
    source = tmp_path / "source.mp3"
    source.touch()
    imported = ImportedAudio(audio_id, source, source.name, "audio/mpeg")
    monkeypatch.setattr(AudioLibrary.instance(), "get", lambda _: imported)
    store = CoverStore()

    info = asyncio.run(store.save_source(audio_id, JPEG_BYTES))

    assert info.source == "source"
    assert store.get(audio_id, "track-one").source == "source"
    assert store.get(audio_id, "track-two").path == store.get(audio_id, "track-one").path

    asyncio.run(store.remove(audio_id, "track-one"))
    with pytest.raises(CoverError):
        store.get(audio_id, "track-one")
    assert store.get(audio_id, "track-two").source == "source"

    manual = asyncio.run(store.save_bytes(audio_id, "track-one", JPEG_BYTES, "manual"))
    assert manual.source == "manual"
    assert store.get(audio_id, "track-one").source == "manual"


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg non disponibile")
def test_flac_writer_embeds_complete_metadata_and_cover(tmp_path: Path) -> None:
    output = tmp_path / "track.flac"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.1",
            "-c:a",
            "flac",
            "-y",
            str(output),
        ],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    cover_path = tmp_path / "cover.jpg"
    cover_path.write_bytes(JPEG_BYTES)
    cover = CoverAsset(cover_path, "image/jpeg", len(JPEG_BYTES), "manual")
    track = Track(
        id="track",
        number=1,
        start_seconds=0,
        end_seconds=0.1,
        artist="Artist",
        title="Title",
        album="Album",
        album_artist="Album Artist",
        track_number=4,
        disc_number=2,
        date="2026",
        genre="Electronic",
        comment="Comment",
        composer="Composer",
        release_group_id="48140466-cff6-3222-bd55-63c27e43190d",
    )

    ExportService._write_flac_tags(output, track, 12, True, cover)
    tagged = FLAC(output)

    assert tagged["title"] == ["Title"]
    assert tagged["albumartist"] == ["Album Artist"]
    assert tagged["tracknumber"] == ["4"]
    assert tagged["tracktotal"] == ["12"]
    assert tagged["discnumber"] == ["2"]
    assert tagged["genre"] == ["Electronic"]
    assert tagged["composer"] == ["Composer"]
    assert tagged["musicbrainz_releasegroupid"] == [
        "48140466-cff6-3222-bd55-63c27e43190d"
    ]
    assert len(tagged.pictures) == 1
    assert tagged.pictures[0].data == JPEG_BYTES
