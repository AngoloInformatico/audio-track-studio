"""Atomic filesystem storage for saved projects and recovery snapshots."""

import os
import re
from pathlib import Path

from pydantic import ValidationError

from backend.core.config import Settings, get_settings
from backend.metadata.filenames import safe_display_name
from backend.projects.models import ProjectDocument, ProjectSummary


class ProjectStorageError(RuntimeError):
    """Raised when a project file cannot be validated or persisted."""


class ProjectStorage:
    maximum_project_bytes = 64 * 1024 * 1024

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.ensure_directories()

    def save(self, document: ProjectDocument, existing_path: Path | None = None) -> Path:
        path = existing_path or self.settings.project_dir / self._filename(document.name, document.id)
        self._require_inside(path, self.settings.project_dir)
        self._write_atomic(path, document)
        return path

    def save_recovery(self, audio_id: str, document: ProjectDocument) -> Path:
        if not re.fullmatch(r"[0-9A-Za-z_-]{1,100}", audio_id):
            raise ProjectStorageError("Identificatore recovery non valido.")
        path = self.settings.recovery_dir / f"{audio_id}.atsproject"
        self._write_atomic(path, document)
        return path

    def remove_recovery(self, audio_id: str) -> None:
        path = self.settings.recovery_dir / f"{audio_id}.atsproject"
        self._require_inside(path, self.settings.recovery_dir)
        path.unlink(missing_ok=True)

    def list_saved(self) -> list[tuple[ProjectSummary, Path]]:
        return self._scan(self.settings.project_dir, "saved")

    def list_recoveries(self) -> list[tuple[ProjectSummary, Path]]:
        return self._scan(self.settings.recovery_dir, "recovery")

    def find_saved(self, project_id: str) -> tuple[ProjectDocument, Path] | None:
        return self._find(self.list_saved(), project_id)

    def find_recovery(self, recovery_id: str) -> tuple[ProjectDocument, Path] | None:
        return self._find(self.list_recoveries(), recovery_id)

    def load_path(self, path: Path) -> ProjectDocument:
        try:
            size = path.stat().st_size
        except OSError as exc:
            raise ProjectStorageError("Il file progetto non è disponibile.") from exc
        if size <= 0 or size > self.maximum_project_bytes:
            raise ProjectStorageError("Il progetto è vuoto o supera il limite di 64 MB.")
        try:
            return ProjectDocument.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValidationError, ValueError) as exc:
            raise ProjectStorageError(
                "Il file .atsproject non è valido o usa una versione non supportata."
            ) from exc

    def load_bytes(self, data: bytes) -> ProjectDocument:
        if not data or len(data) > self.maximum_project_bytes:
            raise ProjectStorageError("Il progetto è vuoto o supera il limite di 64 MB.")
        try:
            return ProjectDocument.model_validate_json(data)
        except (ValidationError, ValueError) as exc:
            raise ProjectStorageError(
                "Il file .atsproject non è valido o usa una versione non supportata."
            ) from exc

    def _scan(
        self, directory: Path, kind: str
    ) -> list[tuple[ProjectSummary, Path]]:
        projects: list[tuple[ProjectSummary, Path]] = []
        for path in directory.glob("*.atsproject"):
            try:
                document = self.load_path(path)
            except ProjectStorageError:
                continue
            projects.append((self.summary(document, kind), path))
        projects.sort(key=lambda item: item[0].updated_at, reverse=True)
        return projects[:20]

    @staticmethod
    def summary(document: ProjectDocument, kind: str = "saved") -> ProjectSummary:
        return ProjectSummary(
            id=document.id,
            name=document.name,
            source_name=document.source.name,
            created_at=document.created_at,
            updated_at=document.updated_at,
            track_count=len(document.tracks),
            has_covers=bool(document.covers),
            kind=kind,
            download_url=f"/api/projects/{document.id}/download" if kind == "saved" else None,
        )

    def _find(
        self, entries: list[tuple[ProjectSummary, Path]], project_id: str
    ) -> tuple[ProjectDocument, Path] | None:
        match = next(((summary, path) for summary, path in entries if summary.id == project_id), None)
        if match is None:
            return None
        _, path = match
        return self.load_path(path), path

    @staticmethod
    def _filename(name: str, project_id: str) -> str:
        clean = safe_display_name(name)
        if clean.lower().endswith(".atsproject"):
            clean = clean[:-11]
        clean = clean.strip(". ") or "Progetto"
        return f"{clean[:120]}-{project_id[:8]}.atsproject"

    def _write_atomic(self, path: Path, document: ProjectDocument) -> None:
        temporary = path.with_name(f".{path.name}.tmp")
        payload = document.model_dump_json(indent=2).encode("utf-8")
        if len(payload) > self.maximum_project_bytes:
            raise ProjectStorageError("Il progetto supera il limite di 64 MB.")
        try:
            temporary.write_bytes(payload)
            os.replace(temporary, path)
        except OSError as exc:
            raise ProjectStorageError(f"Impossibile salvare il progetto: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _require_inside(path: Path, root: Path) -> None:
        resolved_path = path.resolve(strict=False)
        resolved_root = root.resolve(strict=False)
        if resolved_path.parent != resolved_root:
            raise ProjectStorageError("Percorso progetto non consentito.")
