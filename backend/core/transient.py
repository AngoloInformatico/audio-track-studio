"""Cleanup for replaceable audio and embedded-browser working data."""

import shutil
from contextlib import suppress
from pathlib import Path

from backend.core.config import Settings


class TransientStorageError(RuntimeError):
    """Raised instead of deleting an unsafe or unexpectedly broad path."""


def _require_safe_child(base: Path, child: Path) -> None:
    resolved_base = base.resolve(strict=False)
    resolved_parent = child.parent.resolve(strict=False)
    anchor = Path(resolved_base.anchor)
    if resolved_base in {anchor, Path.home().resolve(strict=False)}:
        raise TransientStorageError(f"Percorso temporaneo non sicuro: {resolved_base}")
    if resolved_parent != resolved_base:
        raise TransientStorageError(f"Percorso temporaneo inatteso: {child}")


def clear_directory(path: Path, *, recreate: bool = False) -> None:
    """Remove one explicitly selected transient directory and optionally recreate it."""

    if path.is_symlink():
        path.unlink(missing_ok=True)
    else:
        shutil.rmtree(path, ignore_errors=True)
    if recreate:
        path.mkdir(parents=True, exist_ok=True)


def clear_legacy_transient_storage(settings: Settings) -> None:
    """Remove cache locations used by releases that stored working data in AppData."""

    legacy_cache = settings.data_dir / "cache"
    legacy_webview = settings.data_dir / "webview"
    _require_safe_child(settings.data_dir, legacy_cache)
    _require_safe_child(settings.data_dir, legacy_webview)
    clear_directory(legacy_cache)
    clear_directory(legacy_webview)


def reset_audio_cache(settings: Settings) -> None:
    _require_safe_child(settings.runtime_dir, settings.cache_dir)
    clear_directory(settings.cache_dir, recreate=True)


def reset_webview_cache(settings: Settings) -> None:
    _require_safe_child(settings.runtime_dir, settings.webview_dir)
    clear_directory(settings.webview_dir, recreate=True)


def clear_runtime_storage(settings: Settings) -> None:
    _require_safe_child(settings.runtime_dir, settings.cache_dir)
    _require_safe_child(settings.runtime_dir, settings.webview_dir)
    clear_directory(settings.cache_dir)
    clear_directory(settings.webview_dir)
    with suppress(OSError):
        settings.runtime_dir.rmdir()
