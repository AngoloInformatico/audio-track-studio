import asyncio
import json
import zipfile
from pathlib import Path

import pytest

from backend.core.config import get_settings, update_user_config
from backend.models.recognition import AcoustIDSetupUpdate
from backend.recognition.acoustid import AcoustIDProvider
from backend.recognition.setup import AcoustIDSetupError, AcoustIDSetupService


def test_user_setup_is_persisted_without_exposing_the_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("ACOUSTID_API_KEY", raising=False)
    monkeypatch.delenv("ATS_FPCALC_BINARY", raising=False)
    get_settings.cache_clear()
    fpcalc = tmp_path / "fpcalc.exe"
    fpcalc.write_bytes(b"test executable")

    async def inspect_binary(_: AcoustIDProvider) -> str:
        return "fpcalc version 1.6.1"

    monkeypatch.setattr(AcoustIDProvider, "_inspect_fpcalc", inspect_binary)
    service = AcoustIDSetupService()
    status = asyncio.run(
        service.update(
            AcoustIDSetupUpdate(acoustid_api_key="private-key", fpcalc_path=str(fpcalc))
        )
    )
    payload = json.loads((tmp_path / "data" / "config.json").read_text(encoding="utf-8"))

    assert payload["acoustid_api_key"] == "private-key"
    assert payload["fpcalc_path"] == str(fpcalc.resolve())
    assert "private-key" not in status.model_dump_json()
    get_settings.cache_clear()


def test_update_user_config_preserves_existing_values(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ATS_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()

    update_user_config({"export_directory": "D:/Music"})
    update_user_config({"acoustid_api_key": "key"})
    payload = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))

    assert payload == {"export_directory": "D:/Music", "acoustid_api_key": "key"}
    get_settings.cache_clear()


def test_archive_extraction_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("../fpcalc.exe", b"unsafe")

    with pytest.raises(AcoustIDSetupError, match="percorsi non sicuri"):
        AcoustIDSetupService._extract_archive(archive, tmp_path / "output")


def test_archive_extraction_finds_fpcalc(tmp_path: Path) -> None:
    archive = tmp_path / "chromaprint.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("chromaprint/fpcalc.exe", b"executable")
        package.writestr("chromaprint/COPYING.txt", b"license")

    fpcalc = AcoustIDSetupService._extract_archive(archive, tmp_path / "output")

    assert fpcalc == tmp_path / "output" / "chromaprint" / "fpcalc.exe"
    assert fpcalc.read_bytes() == b"executable"
