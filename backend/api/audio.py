"""Audio import, inspection, streaming, and cleanup endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.audio.ffmpeg_service import FFmpegError, FFmpegService
from backend.audio.library import AudioLibrary, AudioLibraryError
from backend.metadata.cover import CoverError, CoverStore
from backend.metadata.source import read_source_metadata
from backend.models.audio import AudioSession
from backend.tracks.store import TrackStore, TrackStoreError

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/open", response_model=AudioSession, status_code=status.HTTP_201_CREATED)
async def open_audio(file: Annotated[UploadFile, File()]) -> AudioSession:
    """Import an audio file without loading the complete source into memory."""

    library = AudioLibrary.instance()
    imported = None
    try:
        imported = await library.import_upload(file)
        info = await FFmpegService().probe(imported.path, imported.original_name)
        source_metadata = await asyncio.to_thread(
            read_source_metadata,
            imported.path,
            imported.original_name,
        )
        source_cover = None
        if source_metadata.cover_data:
            try:
                source_cover = await CoverStore.instance().save_source(
                    imported.id,
                    source_metadata.cover_data,
                )
            except CoverError:
                # Invalid or unusually large embedded artwork must not block audio import.
                source_cover = None
        TrackStore.instance().initialize(
            imported.id,
            info.duration_seconds,
            default_artist=source_metadata.artist,
            source_cover=source_cover,
        )
        for stale_id in library.ids():
            if stale_id == imported.id:
                continue
            await library.remove(stale_id)
            CoverStore.instance().remove_session(stale_id)
            TrackStore.instance().remove(stale_id)
        return AudioSession(id=imported.id, info=info, stream_url=f"/api/audio/{imported.id}/stream")
    except AudioLibraryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except FFmpegError as exc:
        if imported is not None:
            await library.remove(imported.id)
            CoverStore.instance().remove_session(imported.id)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except TrackStoreError as exc:
        if imported is not None:
            await library.remove(imported.id)
            CoverStore.instance().remove_session(imported.id)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        await file.close()


@router.get("/{audio_id}/stream", response_class=FileResponse)
async def stream_audio(audio_id: str) -> FileResponse:
    """Serve an imported audio file with HTTP range support provided by Starlette."""

    try:
        item = AudioLibrary.instance().get(audio_id)
    except AudioLibraryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(
        item.path,
        media_type=item.media_type,
        filename=item.original_name,
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_audio(audio_id: str) -> None:
    """Remove the managed working copy for an imported source."""

    try:
        await AudioLibrary.instance().remove(audio_id)
        CoverStore.instance().remove_session(audio_id)
        TrackStore.instance().remove(audio_id)
    except AudioLibraryError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
