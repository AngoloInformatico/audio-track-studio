from pathlib import Path

import pytest

from backend.core.config import Settings
from backend.export.service import ExportError, ExportService
from backend.metadata.cover import CoverAsset
from backend.metadata.filenames import render_track_filename
from backend.models.tracks import Track


def test_track_filename_uses_fallbacks_and_windows_sanitization() -> None:
    assert render_track_filename(
        "{track:02d} - {artist} - {title}.flac",
        track=3,
        artist="AC/DC",
        title="Song: Live?",
    ) == "03 - AC_DC - Song_ Live_.flac"
    assert render_track_filename("{title}", track=1, artist="", title="") == "Traccia 01.flac"


def test_track_filename_rejects_unknown_placeholder() -> None:
    with pytest.raises(ValueError, match="Placeholder non supportato"):
        render_track_filename("{album} - {title}", track=1, artist="A", title="T")
    with pytest.raises(ValueError, match="Schema nome file non valido"):
        render_track_filename("{track:02d - {title}", track=1, artist="A", title="T")


def test_export_rejects_duplicate_and_existing_names(tmp_path: Path) -> None:
    service = ExportService(Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "out"))
    with pytest.raises(ExportError, match="duplicati"):
        service._validate_outputs(tmp_path, ["Track.flac", "track.flac"], overwrite=False)

    (tmp_path / "01.flac").write_bytes(b"existing")
    with pytest.raises(ExportError, match="esiste già"):
        service._validate_outputs(tmp_path, ["01.flac"], overwrite=False)


def test_export_destination_must_not_be_cache_or_disk_root(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "app", default_export_dir=tmp_path / "out")
    service = ExportService(settings)
    settings.cache_dir.mkdir(parents=True)

    with pytest.raises(ExportError, match="cache applicativa"):
        service._prepare_destination(str(settings.cache_dir / "exports"))

    with pytest.raises(ExportError, match="radice del disco"):
        service._prepare_destination(str(Path(tmp_path.anchor)))


def test_cover_filenames_are_unambiguous(tmp_path: Path) -> None:
    first = Track(id="a", number=1, start_seconds=0, end_seconds=1)
    second = Track(id="b", number=2, start_seconds=1, end_seconds=2)
    jpeg = CoverAsset(tmp_path / "a.jpg", "image/jpeg", 1, "manual")
    png = CoverAsset(tmp_path / "b.png", "image/png", 1, "manual")

    assert ExportService._cover_filenames([(first, jpeg)]) == ["cover.jpg"]
    assert ExportService._cover_filenames([(first, jpeg), (second, png)]) == [
        "01 - cover.jpg",
        "02 - cover.png",
    ]
