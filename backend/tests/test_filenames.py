import pytest

from backend.metadata.filenames import safe_display_name


def test_safe_display_name_removes_paths_and_invalid_characters() -> None:
    assert safe_display_name(r"C:\music\mix<live>.mp3") == "mix_live_.mp3"


def test_safe_display_name_rejects_empty_name() -> None:
    with pytest.raises(ValueError):
        safe_display_name("...")
