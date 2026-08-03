"""Automatic audio boundary analysis endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.analysis.service import AnalysisError, AnalysisService
from backend.core.jobs import JobManager
from backend.models.analysis import AnalysisConfig, AnalysisRequest
from backend.models.jobs import JobView

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/config", response_model=AnalysisConfig)
async def get_analysis_config() -> AnalysisConfig:
    return AnalysisConfig()


@router.post("/start", response_model=JobView, status_code=status.HTTP_202_ACCEPTED)
async def start_analysis(request: AnalysisRequest) -> JobView:
    service = AnalysisService()
    try:
        service.validate_source(request.audio_id)
    except AnalysisError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    async def run(report):
        return await service.analyze(request, report)

    return JobManager.instance().start("analysis", run)
