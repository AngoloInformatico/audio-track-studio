import base64
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from mutagen.flac import FLAC, Picture

from backend.metadata import source

JPEG_BYTES = b"\xff\xd8\xff\xe0source-cover\xff\xd9"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


class FakeTags(dict):
    def getall(self, key: str) -> list[object]:
        return list(self.get(f"frames:{key}", []))


def test_source_metadata_uses_title_when_artist_is_missing(monkeypatch) -> None:
    audio = SimpleNamespace(
        tags=FakeTags(
            {
                "TIT2": SimpleNamespace(text=["AI Collection"]),
                "frames:APIC": [SimpleNamespace(data=JPEG_BYTES)],
            }
        ),
        pictures=[],
    )
    monkeypatch.setattr(source, "MutagenFile", lambda _path: audio)

    metadata = source.read_source_metadata(Path("source.mp3"), "original.mp3")

    assert metadata.title == "AI Collection"
    assert metadata.artist == "AI Collection"
    assert metadata.cover_data == JPEG_BYTES


def test_source_metadata_prefers_artist_and_front_cover(monkeypatch) -> None:
    front = SimpleNamespace(type=3, data=JPEG_BYTES)
    other = SimpleNamespace(type=4, data=b"other")
    audio = SimpleNamespace(
        tags=FakeTags(
            {
                "title": ["Source title"],
                "artist": ["Source artist"],
            }
        ),
        pictures=[other, front],
    )
    monkeypatch.setattr(source, "MutagenFile", lambda _path: audio)

    metadata = source.read_source_metadata(Path("source.flac"), "original.flac")

    assert metadata.title == "Source title"
    assert metadata.artist == "Source artist"
    assert metadata.cover_data == JPEG_BYTES


def test_source_metadata_falls_back_to_filename(monkeypatch) -> None:
    monkeypatch.setattr(source, "MutagenFile", lambda _path: None)

    metadata = source.read_source_metadata(Path("source.wav"), "Generated Mix.wav")

    assert metadata.title == "Generated Mix"
    assert metadata.artist == "Generated Mix"
    assert metadata.cover_data is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="FFmpeg non disponibile")
def test_source_metadata_reads_real_flac_tags_and_picture(tmp_path: Path) -> None:
    audio_path = tmp_path / "generated.flac"
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
            str(audio_path),
        ],
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    tagged = FLAC(audio_path)
    tagged["title"] = "AI Source Title"
    picture = Picture()
    picture.type = 3
    picture.mime = "image/png"
    picture.data = PNG_BYTES
    tagged.add_picture(picture)
    tagged.save()

    metadata = source.read_source_metadata(audio_path, audio_path.name)

    assert metadata.artist == "AI Source Title"
    assert metadata.cover_data == PNG_BYTES
