"""Application health endpoints."""

from fastapi import APIRouter

from backend import __version__
from backend.audio.ffmpeg_service import FFmpegService
from backend.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Report API status and local multimedia dependency availability."""

    tools = await FFmpegService().inspect_tools()
    return HealthResponse(version=__version__, tools=tools)
