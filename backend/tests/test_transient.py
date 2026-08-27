from pathlib import Path

import pytest

from backend.core.config import Settings
from backend.core.transient import (
    TransientStorageError,
    clear_legacy_transient_storage,
    clear_runtime_storage,
    reset_audio_cache,
)


def test_transient_cleanup_preserves_projects_and_configuration(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        runtime_dir=tmp_path / "runtime",
        default_export_dir=tmp_path / "exports",
    )
    settings.ensure_directories()
    project = settings.project_dir / "saved.atsproject"
    project.write_text("project", encoding="utf-8")
    (settings.data_dir / "cache" / "old").mkdir(parents=True)
    (settings.data_dir / "cache" / "old" / "source.flac").write_bytes(b"old")
    (settings.data_dir / "webview" / "Cache").mkdir(parents=True)

    clear_legacy_transient_storage(settings)
    reset_audio_cache(settings)
    (settings.cache_dir / "session").mkdir()
    clear_runtime_storage(settings)

    assert project.is_file()
    assert settings.config_file.is_file()
    assert not (settings.data_dir / "cache").exists()
    assert not (settings.data_dir / "webview").exists()
    assert not settings.runtime_dir.exists()


def test_cleanup_rejects_a_disk_root(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        runtime_dir=Path(tmp_path.anchor),
        default_export_dir=tmp_path / "exports",
    )

    with pytest.raises(TransientStorageError, match="non sicuro"):
        reset_audio_cache(settings)
