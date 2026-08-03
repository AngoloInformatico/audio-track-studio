"""FLAC export job endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.core.config import get_settings
from backend.core.jobs import JobManager
from backend.export.service import ExportError, ExportService
from backend.models.export import ExportConfig, ExportRequest
from backend.models.jobs import JobView

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/config", response_model=ExportConfig)
async def get_export_config() -> ExportConfig:
    return ExportConfig(default_directory=str(get_settings().default_export_dir))


@router.post("/start", response_model=JobView, status_code=status.HTTP_202_ACCEPTED)
async def start_export(request: ExportRequest) -> JobView:
    service = ExportService()
    try:
        service.validate_source(request.audio_id)
    except ExportError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    async def run(report):
        return await service.export(request, report)

    return JobManager.instance().start("export", run)
