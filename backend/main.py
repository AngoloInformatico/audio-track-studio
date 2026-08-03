"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend import __version__
from backend.api.analysis import router as analysis_router
from backend.api.audio import router as audio_router
from backend.api.export import router as export_router
from backend.api.health import router as health_router
from backend.api.jobs import router as jobs_router
from backend.api.projects import router as projects_router
from backend.api.recognition import router as recognition_router
from backend.api.tracks import router as tracks_router
from backend.core.config import get_settings
from backend.core.logging import configure_logging, get_logger
from backend.core.resources import resource_path


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize application services without blocking startup."""

    configure_logging()
    settings = get_settings()
    settings.ensure_directories()
    get_logger(__name__).info("Audio Track Studio backend started")
    yield
    get_logger(__name__).info("Audio Track Studio backend stopped")


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Local API for Audio Track Studio.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(audio_router, prefix=settings.api_prefix)
app.include_router(tracks_router, prefix=settings.api_prefix)
app.include_router(analysis_router, prefix=settings.api_prefix)
app.include_router(recognition_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(export_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)

frontend_directory = resource_path("frontend", "dist")
if (frontend_directory / "index.html").is_file():
    app.mount("/", StaticFiles(directory=frontend_directory, html=True), name="frontend")
