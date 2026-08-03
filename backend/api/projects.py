"""Project save, inspection, relink, recent, and recovery endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.projects.models import (
    ProjectApplyRequest,
    ProjectApplyResult,
    ProjectAutosaveRequest,
    ProjectPrepareRequest,
    ProjectPreview,
    ProjectSaveRequest,
    ProjectSaveResult,
    ProjectSummary,
)
from backend.projects.service import ProjectError, ProjectService
from backend.projects.storage import ProjectStorage, ProjectStorageError

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/recent", response_model=list[ProjectSummary])
async def list_recent_projects() -> list[ProjectSummary]:
    return [summary for summary, _ in ProjectStorage().list_saved()]


@router.get("/recovery", response_model=list[ProjectSummary])
async def list_recovery_projects() -> list[ProjectSummary]:
    return [summary for summary, _ in ProjectStorage().list_recoveries()]


@router.post("/save", response_model=ProjectSaveResult)
async def save_project(request: ProjectSaveRequest) -> ProjectSaveResult:
    service = ProjectService()
    try:
        summary, path = await asyncio.to_thread(
            service.save,
            request.audio_id,
            request.name,
            request.project_id,
            request.save_as,
            request.settings,
        )
    except (ProjectError, ProjectStorageError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    return ProjectSaveResult(project=summary, path=str(path))


@router.post("/autosave", response_model=ProjectSummary)
async def autosave_project(request: ProjectAutosaveRequest) -> ProjectSummary:
    try:
        return await asyncio.to_thread(
            ProjectService().autosave,
            request.audio_id,
            request.name,
            request.project_id,
            request.settings,
        )
    except (ProjectError, ProjectStorageError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/inspect", response_model=ProjectPreview)
async def inspect_project(file: Annotated[UploadFile, File()]) -> ProjectPreview:
    data = bytearray()
    try:
        while chunk := await file.read(256 * 1024):
            data.extend(chunk)
            if len(data) > ProjectStorage.maximum_project_bytes:
                raise ProjectStorageError("Il progetto supera il limite di 64 MB.")
        document = await asyncio.to_thread(ProjectStorage().load_bytes, bytes(data))
        return ProjectService().prepare(document)
    except (ProjectError, ProjectStorageError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    finally:
        await file.close()


@router.post("/prepare", response_model=ProjectPreview)
async def prepare_saved_project(request: ProjectPrepareRequest) -> ProjectPreview:
    storage = ProjectStorage()
    if request.project_id:
        found = storage.find_saved(request.project_id)
        persisted_id = request.project_id
    else:
        found = storage.find_recovery(request.recovery_id or "")
        recovery_document = found[0] if found else None
        persisted_id = (
            recovery_document.id
            if recovery_document and storage.find_saved(recovery_document.id)
            else None
        )
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")
    document, _ = found
    try:
        return ProjectService(storage).prepare(document, persisted_id)
    except ProjectError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.post("/apply", response_model=ProjectApplyResult)
async def apply_project(request: ProjectApplyRequest) -> ProjectApplyResult:
    try:
        return await ProjectService().apply(request.token, request.audio_id)
    except ProjectError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.get("/{project_id}/download", response_class=FileResponse)
async def download_project(project_id: str) -> FileResponse:
    found = ProjectStorage().find_saved(project_id)
    if found is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progetto non trovato.")
    document, path = found
    return FileResponse(
        path,
        media_type="application/json",
        filename=f"{document.name}.atsproject",
    )
