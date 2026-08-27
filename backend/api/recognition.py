"""Music recognition readiness and job endpoints."""

from fastapi import APIRouter, HTTPException, status

from backend.core.jobs import JobManager
from backend.models.jobs import JobView
from backend.models.recognition import (
    AcoustIDSetupStatus,
    AcoustIDSetupUpdate,
    RecognitionConfig,
    RecognitionRequest,
)
from backend.recognition.acoustid import AcoustIDProvider
from backend.recognition.service import RecognitionError, RecognitionService
from backend.recognition.setup import AcoustIDSetupError, AcoustIDSetupService

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.get("/config", response_model=RecognitionConfig)
async def get_recognition_config() -> RecognitionConfig:
    return await AcoustIDProvider().inspect()


@router.get("/setup", response_model=AcoustIDSetupStatus)
async def get_acoustid_setup() -> AcoustIDSetupStatus:
    return await AcoustIDSetupService().inspect()


@router.put("/setup", response_model=AcoustIDSetupStatus)
async def update_acoustid_setup(request: AcoustIDSetupUpdate) -> AcoustIDSetupStatus:
    try:
        return await AcoustIDSetupService().update(request)
    except AcoustIDSetupError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/setup/install-fpcalc", response_model=AcoustIDSetupStatus)
async def install_fpcalc() -> AcoustIDSetupStatus:
    try:
        return await AcoustIDSetupService().install_fpcalc()
    except AcoustIDSetupError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post("/start", response_model=JobView, status_code=status.HTTP_202_ACCEPTED)
async def start_recognition(request: RecognitionRequest) -> JobView:
    provider = AcoustIDProvider()
    readiness = await provider.inspect()
    if not readiness.available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=readiness.message)
    service = RecognitionService(provider)
    try:
        service.validate_request(request)
    except RecognitionError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    async def run(report):
        return await service.recognize(request, report)

    return JobManager.instance().start("recognition", run)
