"""Manual marker, metadata, and cover editor endpoints."""

from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from backend.metadata.cover import CoverError, CoverStore
from backend.metadata.cover_art_archive import CoverArtArchiveClient
from backend.models.recognition import RecognitionMetadataApply
from backend.models.tracks import (
    CoverArtArchiveRequest,
    MarkerUpdate,
    TrackCollection,
    TrackMetadataUpdate,
)
from backend.tracks.store import TrackStateNotFoundError, TrackStore, TrackStoreError

router = APIRouter(prefix="/audio/{audio_id}", tags=["tracks"])


@router.get("/tracks", response_model=TrackCollection)
async def get_tracks(audio_id: str) -> TrackCollection:
    try:
        return TrackStore.instance().get(audio_id)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/markers", response_model=TrackCollection)
async def replace_markers(audio_id: str, update: MarkerUpdate) -> TrackCollection:
    try:
        return TrackStore.instance().replace_markers(audio_id, update.markers)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrackStoreError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/tracks/{track_id}", response_model=TrackCollection)
async def update_track(
    audio_id: str, track_id: str, update: TrackMetadataUpdate
) -> TrackCollection:
    try:
        return TrackStore.instance().patch_metadata(audio_id, track_id, update)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/tracks", response_model=TrackCollection)
async def apply_recognition_metadata(
    audio_id: str, update: RecognitionMetadataApply
) -> TrackCollection:
    try:
        return TrackStore.instance().update_metadata_batch(audio_id, update.items)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except TrackStoreError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/tracks/{track_id}/cover", response_class=FileResponse)
async def get_track_cover(audio_id: str, track_id: str) -> FileResponse:
    try:
        collection = TrackStore.instance().get(audio_id)
        if not any(track.id == track_id for track in collection.tracks):
            raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
        asset = CoverStore.instance().get(audio_id, track_id)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CoverError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return FileResponse(asset.path, media_type=asset.mime_type)


@router.post("/tracks/{track_id}/cover", response_model=TrackCollection)
async def upload_track_cover(
    audio_id: str,
    track_id: str,
    file: Annotated[UploadFile, File()],
) -> TrackCollection:
    try:
        TrackStore.instance().get(audio_id)
        if not any(track.id == track_id for track in TrackStore.instance().get(audio_id).tracks):
            raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
        cover = await CoverStore.instance().save_upload(audio_id, track_id, file)
        return TrackStore.instance().set_cover(audio_id, track_id, cover)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CoverError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    finally:
        await file.close()


@router.post("/tracks/{track_id}/cover/from-release-group", response_model=TrackCollection)
async def fetch_track_cover(
    audio_id: str,
    track_id: str,
    request: CoverArtArchiveRequest,
) -> TrackCollection:
    try:
        collection = TrackStore.instance().get(audio_id)
        if not any(track.id == track_id for track in collection.tracks):
            raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
        data = await CoverArtArchiveClient().fetch_front(request.release_group_id)
        if data is None:
            raise CoverError("Nessuna copertina disponibile per questa pubblicazione.")
        cover = await CoverStore.instance().save_bytes(
            audio_id,
            track_id,
            data,
            "cover_art_archive",
        )
        return TrackStore.instance().set_cover(audio_id, track_id, cover)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CoverError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/tracks/{track_id}/cover", response_model=TrackCollection)
async def remove_track_cover(audio_id: str, track_id: str) -> TrackCollection:
    try:
        collection = TrackStore.instance().get(audio_id)
        if not any(track.id == track_id for track in collection.tracks):
            raise TrackStateNotFoundError("Traccia non trovata o sessione scaduta.")
        await CoverStore.instance().remove(audio_id, track_id)
        return TrackStore.instance().set_cover(audio_id, track_id, None)
    except TrackStateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CoverError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
